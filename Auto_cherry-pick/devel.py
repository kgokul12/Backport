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

sorted_commits=[]
applied_commits=[]

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
    if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
        os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
    Run_command(f"git config core.editor 'vi'")
    print("cherry-pick aborted...")
    sys.exit(1)

#add commit upstream message.
def Add_upstream_msg(commit):
    if len(sys.argv) > 1 and sys.argv[1] == "-s":
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

# Definition to check the commit is already applied ot not
def Check_commit_status(commit, count):
    if commit == applied_commits[count]:
        # if commit already applied in order skip and return -1 
        return -1
    else :
        # Return the value to reset...
        return len(applied_commits) - count

def Change_core_editor():
    # Create a temporary script to simulate an automated editor
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sh', mode='w') as temp_script:
            temp_script.write("#!/bin/bash\nexit\n")
            temp_script_path = temp_script.name

    # Make the temporary script executable
    os.chmod(temp_script_path, 0o755)

    Run_command(f"git config core.editor {temp_script_path}")

def Get_commit_input(commits):

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
            f.write(f"grep -n {commit} /home/amd/acp_log\n")

def Process_commits(commits):
    global sorted_commits, applied_commits
    # Sort and unique the commit IDs, then prepare the grep commands
    if not os.path.exists("/home/amd/acp_log"):
        print("\nMake a log copy of kernel latest version in Home as acp_log")
        print("    eg : checkout to kernel master branch ")
        print("         git log --pretty=oneline > /home/amd/acp_log")
        sys.exit(1)

    os.chmod(tmpfile, 0o755)

    grep_output = subprocess.run(["bash", tmpfile], stdout=subprocess.PIPE, universal_newlines=True)
    if not grep_output.stdout.strip():
        print("No commits to process.. May be a invalid commit id")
        sys.exit(1)

    # Save the output to a file
    with open(sorted_file, "w") as output_file:
        output_file.write(grep_output.stdout)

    commits = sorted(set(grep_output.stdout.splitlines()), reverse=True)
    
    for line in commits:
            sorted_commits.append(line.split(':')[1].split()[0])
    print("Commits sorted....")

    # Take all the applied commits from the applied file in applied_commits variable
    if os.path.exists(applied):
        cat_output = subprocess.run(["cat", applied], stdout=subprocess.PIPE, universal_newlines=True)
        applied_commits = cat_output.stdout.splitlines()

def Trap_signals():
    # Trapping signal SIGINT and SIGTERM
    signal.signal(signal.SIGINT, Sig_catch)
    signal.signal(signal.SIGTERM, Sig_catch)

def Apply_commits():
    # Applying the commits
    count = 0
    check_val = -1
    for commit in sorted_commits:
        if check_val == -1 and os.path.exists(applied):
            check_val = Check_commit_status(commit,count)
            if check_val == -1:
                count+=1
                continue
            else:
                print(f"==> git reset --hard HEAD~{check_val}")
                Run_command(f"git reset --hard HEAD~{check_val}")
        else:
            check_val = 0
            
        print(f" --> Applying commit {commit} ....")
        result = subprocess.run(["git", "cherry-pick", commit])
        print(result.returncode)
        while result.returncode != 0:
            print(f"\nConflict occurred while applying commit {commit}.")
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
            break
        print(f"Commit {commit} successfully applied....")
        add_upstream_msg(commit)
        Run_command(f"echo {commit} >> {applied}")

    # Display a completion message
    print("All commits have been processed.")

def Reset_editor():
    #Reset editor back to "vim"
    if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
        os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
    Run_command(f"git config core.editor 'vi'")

def Cleanup():
    # Clean up the temporary files
    os.remove(tmpfile)
    os.remove(sorted_file)
    os.remove(applied)
    os.remove(temp_file_path)
    os.remove(temp_script_path)

def Release_signals():
    # Untrap the signals by resetting them to default behavior
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)

def Call_options():
    # clean all the applied commits 
    if sys.argv[1] == "--reset" or sys.argv[1] == "-r" or sys.argv[1] == "-ra":
        if sys.argv[1] == "-ra" or sys.argv[2] == "all":
            if os.path.exists(applied):
                with open(applied, 'r') as file:
                    count = sum(1 for line in file)
                print(f"==> git reset --hard HEAD~{count}")
                Run_command(f"git reset --hard HEAD~{count}")
                print("cleaning all Applied commits")
                os.remove(applied)
            sys.exit(0)
        else :
            print(f"==> git reset --hard HEAD~{int(sys.argv[2])}")
            Run_command(f"git reset --hard HEAD~{int(sys.argv[2])}")
                    
    # show list of commits with order
    elif sys.argv[1] == "--list" or sys.argv[1] == "-l":
        print("The list of commits in QUEUE are:")
        Run_command(f"cat {sorted_file}")
        sys.exit(0)
            
    # To clean the tmpfiles to start new set of patches
    elif sys.argv[1] == "--clean" or sys.argv[1] == "-c":
        # Clean up the temporary files
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        if os.path.exists(sorted_file):
            os.remove(sorted_file)
        if os.path.exists(applied):
            os.remove(applied)
        print("Cleaning done successfully..")
        sys.exit(0)
       
    # To add any found dependent commit
    elif sys.argv[1] == "--add" or sys.argv[1] == "-a":
        if len(sys.argv) < 3:
            print("Add commit id too")
            print("    Eg : acp -a <commit id1> <commit id2> <commit id3>...")
            sys.exit(1)
        for i in range(2, len(sys.argv)+1):
            Run_command(f"echo {sys.argv[i]} >> {tmpfile}")
            i+=1
        print("Added successfully to list....")
        sys.exit(0)
        
    else :
        print("Invalid option..")
        sys.exit(1)
        
def main():
    if len(sys.argv) > 0 and not sys.argv[1] == "-s":
        call_options()

    # Initialize a list to hold the commit IDs
    commits = []
    #get input commits, process, sort and save into sorted_commits...
    Get_commit_input(commits)
    
    Process_commits(commits)

    Trap_signals()

    Change_core_editor()

    Apply_commits()

    Reset_editor()

    Release_signals()

    Cleanup()

if __name__ == "__main__":
    main()

