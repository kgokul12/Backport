#!/usr/bin/env python3
import os
import subprocess
import signal
import sys
import tempfile

# Define temporary files
tmpfile = "/tmp/commits"
applied = "/tmp/applied"
sorted_file = "/tmp/sorted"
acp_log = "/home/amd/acp_log"

sorted_commits=[]
applied_commits=[]
Sign_off_flag = False
Continue_flag = False

def Run_command(command):
    """Run a shell command and handle errors."""
    result = subprocess.run(command, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    if result.returncode != 0:
        print(result.stderr)
        print(f"Error: Command failed: {command}")
        exit(1)

# Function to handle trapped signals
def Sig_catch(signum, frame):
    print("Processing Interrupt...")
    Run_command("git cherry-pick --abort")
    Reset_editor()
    print("cherry-pick aborted...")
    sys.exit(1)

def Trap_signals():
    # Trapping signal SIGINT and SIGTERM
    signal.signal(signal.SIGINT, Sig_catch)
    signal.signal(signal.SIGTERM, Sig_catch)

def Release_signals():
    # Untrap the signals by resetting them to default behavior
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

def Change_core_editor():
    global temp_script_path 
    # Create a temporary script to simulate an automated editor
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sh', mode='w') as temp_script:
            temp_script.write("#!/bin/bash\nexit\n")
            temp_script_path = temp_script.name

    # Make the temporary script executable
    os.chmod(temp_script_path, 0o755)

    Run_command(f"git config core.editor {temp_script_path}")

def Reset_editor():
    #Reset editor back to "vim"
    if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
        os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
    Run_command(f"git config core.editor 'vi'")
    os.remove(temp_file_path)
    os.remove(temp_script_path)

#add commit upstream message.
def Add_upstream_msg(commit):
    global temp_file_path
    if Sign_off_flag:
        # Run `git commit --amend -s`
        print("Adding sign-off content...")
        Run_command("git commit --amend -s")

    # Modify the commit message to include the SHA_ID and additional text
    commit_message = subprocess.check_output("git log -1 --pretty=%B", shell=True, universal_newlines=True).strip()

    # Split the commit message into the first line and the rest
    lines = commit_message.split('\n', 1)
    first_line = lines[0]
    rest_of_message = lines[1] if len(lines) > 1 else ""

    # Combine the new messageg
    new_commit_message = f"{first_line}\n\ncommit {commit} upstream\n\n{rest_of_message}"

    # Write the new commit message to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        temp_file.write(new_commit_message)
        temp_file_path = temp_file.name

    # Amend the commit with the new message
    print("Adding upstream commit message...")
    Run_command(f"git commit --amend --file={temp_file_path}")

def Get_commit_input():
    commits=[]
    # Read multiple lines of commit IDs into the 'commits' list
    print("Enter the commit IDs (one per line). Press Ctrl+D when done:")
    try:
        while True:
            line = input()
            if line:
                commits.append(line)
    except EOFError:
        pass
        
    with open(tmpfile, "w") as f:
        for commit in commits:
            f.write(f"grep -n {commit} {acp_log}\n")

def Process_commits():
    global sorted_commits, applied_commits
    # Sort and unique the commit IDs, then prepare the grep commands
    if not os.path.exists(acp_log):
        print(f"\nMake a log copy of kernel latest version in Home as {acp_log}")
        print("    eg : checkout to kernel master branch ")
        print(f"         git log --pretty=oneline > {acp_log}")
        sys.exit(1)

    os.chmod(tmpfile, 0o755)

    grep_output = subprocess.run(["bash", tmpfile], stdout=subprocess.PIPE, universal_newlines=True)
    if not grep_output.stdout.strip():
        print("No commits to process.. May be a invalid commit id")
        sys.exit(1)

    commits = sorted(set(grep_output.stdout.splitlines()), reverse=True)
    
    # Save the output to a file
    with open(sorted_file, "w") as output_file:
        for commit in commits:
            output_file.write(f"{commit}\n")
    
    for line in commits:
            sorted_commits.append(line.split(':')[1].split()[0])
    print("Commits sorted....")

    # Take all the applied commits from the applied file in applied_commits variable
    if os.path.exists(applied):
        cat_output = subprocess.run(["cat", applied], stdout=subprocess.PIPE, universal_newlines=True)
        applied_commits = cat_output.stdout.splitlines()

# Definition to check the commit is already applied ot not
def Check_commit_status(commit, count):
    if commit in applied_commits and commit == applied_commits[count]:
        # if commit already applied in order skip and return -1 
        return -1
    else :
        # Return the value to reset...
        return len(applied_commits) - count

def Apply_commits():
    # Applying the commits
    count = 0
    check_val = -1
    for commit in sorted_commits:
        if check_val == -1:
            check_val = Check_commit_status(commit, count)
            if check_val == -1:
                count += 1
                continue
            else:
                print(f"git reset --hard HEAD~{check_val}")
                Run_command(f"git reset --hard HEAD~{check_val}")
                check_val  = 0
                
        print(f" --> Applying commit {commit} ....")
        result = subprocess.run(["git", "cherry-pick", commit])
        print(result.returncode)
        if result.returncode != 0:
            print(f"\nConflict occurred while applying commit {commit}")
            print("Resolve the conflict and enter \n'done' / 'd' --> continue \n'abort' / 'a' --> cancel \n'bash' / 'b' --> open bash\n")

            try:
                while True:
                    user_input = input().strip().lower()
                    if user_input == "done" or user_input == 'd':
                        Run_command("git add -u")
                        Run_command("git cherry-pick --continue")
                        break
                    elif user_input == "abort" or user_input == 'a':
                        if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
                            os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
                        Reset_editor()
                        Run_command(f"git config core.editor 'vi'")
                        Run_command("git cherry-pick --abort")
                        sys.exit(1)
                    elif user_input == "bash" or user_input == 'b':
                        print("Entering bash mode... to come out enter 'exit'")
                        subprocess.run("bash")
                    else :
                        print("Invalid input...")
            except EOFError:
                break
        print(f"Commit {commit} successfully applied....")
        Add_upstream_msg(commit)
        Run_command(f"echo {commit} >> {applied}")
                
    # Display a completion message
    print("All commits have been processed.")

def Cleanup():
    # Clean up the temporary files
    os.remove(tmpfile)
    os.remove(sorted_file)
    if os.path.exists(applied):
        os.remove(applied)
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    os.remove(temp_script_path)
    
def Call_options():
    global Sign_off_flag, Continue_flag
    
    if sys.argv[1] in ["--reset", "-r", "-ra"]:
        if sys.argv[1] in ["-ra", "--reset"] and len(sys.argv) > 2 and sys.argv[2] == "all":
            if os.path.exists(applied):
                with open(applied, 'r') as file:
                    count = sum(1 for line in file)
                print(f"==> git reset --hard HEAD~{count}")
                Run_command(f"git reset --hard HEAD~{count}")
                print("Cleaning all applied commits")
                os.remove(applied)
            sys.exit(0)
        else:
            try:
                # Try to convert sys.argv[2] to an integer
                reset_value = int(sys.argv[2])
                print(f"==> git reset --hard HEAD~{reset_value}")
                Run_command(f"git reset --hard HEAD~{reset_value}")
            except ValueError:
                # If conversion fails, it's not an integer, so treat it as a commit hash
                print(f"==> git reset --hard {sys.argv[2]}")
                Run_command(f"git reset --hard {sys.argv[2]}")
            sys.exit(0)

    elif sys.argv[1] in ["--status", "-s"]:
        if not os.path.exists(sorted_file):
            print("Nothing in list to show")
            sys.exit(0)
        print("\nThe list of commits in QUEUE are:\n")
        Run_command(f"cat {sorted_file}")
        if not os.path.exists(applied):
            print("\nNo commits applied yet\n")
            sys.exit(0)
        print("\nThe list of commits already applied:\n")
        Run_command(f"cat {applied}")
        sys.exit(0)

    elif sys.argv[1] in ["--list", "-l"]:
        Process_commits()
        if os.path.exists(sorted_file):
            print("The list of commits in QUEUE are:")
            Run_command(f"cat {sorted_file}")
            sys.exit(0)
        else:
            print("Nothing added to list")
            sys.exit(1)

    elif sys.argv[1] in ["--clean", "-c"]:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        if os.path.exists(sorted_file):
            os.remove(sorted_file)
        if os.path.exists(applied):
            os.remove(applied)
        print("Cleaning done successfully..")
        sys.exit(0)

    elif sys.argv[1] in ["--add", "-a"]:
        if len(sys.argv) < 3:
            print("Add commit id:")
            print("    Eg : acp -a <commit id1> <commit id2> <commit id3>...")
            sys.exit(1)
        for i in range(2, len(sys.argv)):
            Run_command(f"echo \"grep -n {sys.argv[i]} {acp_log}\" >> {tmpfile}")
        print("Added successfully to list....")
        sys.exit(0)

    elif sys.argv[1] in ["--signoff", "-S"]:
        Sign_off_flag = True

    elif sys.argv[1] in ["--continue", "-C"]:
        Continue_flag = True
        
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("     acp [optoins] (-s, -l, -c, -r)")
        print("     acp [options] <commit> (-a)")
        print("         -s or --status   --> to check the status of applied commits and list of commits in order")
        print("         -S or --Signoff  --> to add signoff message to the commit log")
        print("         -l or --list     --> to check the list of ordered commit ids")
        print("         -c or --clean    --> to clear of logs of cherry-pick")
        print("         -C or --continue    --> to clear of logs of cherry-pick")
        print("         -r or --reset    --> to reset the logs")
        print("                          --> -ra or --reset all to reset all the applied commits")
        print("         -a or -add       --> to add a commit id to the list")
        
    else:
        print("Invalid option... See help")
        sys.exit(1)
   
if __name__ == "__main__":
    if len(sys.argv) > 1:
        Call_options()

    if Continue_flag:
        if not os.path.exists(tmpfile):
            print("Add input commits first...")
            #get input commits, process, sort and save into sorted_commits...
            Get_commit_input()
        else :                
            Process_commits()
    else :
        #get input commits, process, sort and save into sorted_commits...
        Get_commit_input()
        Process_commits()
      
    Trap_signals()

    Change_core_editor()

    Apply_commits()

    Reset_editor()

    Release_signals()

    Cleanup()

