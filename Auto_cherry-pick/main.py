#!/usr/bin/env python3
import os
import subprocess
import signal
import sys
import tempfile

# Define temporary files
tmpfile = "/tmp/commits"

def run_command(command):
    """Run a shell command and handle errors."""
    result = subprocess.run(command, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    if result.returncode != 0:
        print(result.stderr)
        print(f"Error: Command failed: {command}")
        exit(1)

# Function to handle trapped signals
def clear_cp(signum, frame):
    print("Processing Interrupt...")
    run_command("git cherry-pick --abort")
    if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
        os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
    run_command(f"git config core.editor 'vi'") 
    print("cherry-pick aborted...")
    sys.exit(1)

#add commit upstream message.
def add_upstream_msg(commit):
    if len(sys.argv) > 1 and sys.argv[1] == "-s":
        # Run `git commit --amend -s`
        run_command("git commit --amend -s")

    # Modify the commit message to include the SHA_ID and additional text
    commit_message = subprocess.check_output("git log -1 --pretty=%B", shell=True, universal_newlines=True).strip()

    # Split the commit message into the first line and the rest
    lines = commit_message.split('\n', 1)
    first_line = lines[0]
    rest_of_message = lines[1] if len(lines) > 1 else ""

    # Combine the new message
    new_commit_message = f"{first_line}\n\ncommit {commit} upstream\n\n{rest_of_message}"

    # Write the new commit message to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
        temp_file.write(new_commit_message)
        temp_file_path = temp_file.name

    # Amend the commit with the new message
    run_command(f"git commit --amend --file={temp_file_path}")

# Create a temporary script to simulate an automated editor
with tempfile.NamedTemporaryFile(delete=False, suffix='.sh', mode='w') as temp_script:
        temp_script.write("#!/bin/bash\nexit\n")
        temp_script_path = temp_script.name

# Make the temporary script executable
os.chmod(temp_script_path, 0o755)

run_command(f"git config core.editor {temp_script_path}")

# Initialize a list to hold the commit IDs
commits = []

# Read multiple lines of commit IDs into the 'commits' list
print("Enter the commit IDs (one per line). Press Ctrl+D when done:")
try:
    while True:
        line = input()
        if line:
            commits.append(line)
except EOFError:
    pass

# Sort and unique the commit IDs, then prepare the grep commands
with open(tmpfile, "w") as f:
    for commit in commits:
        f.write(f"grep -n {commit} ~/log\n")

os.chmod(tmpfile, 0o755)

grep_output = subprocess.run(["bash", tmpfile], stdout=subprocess.PIPE, universal_newlines=True)
if not grep_output.stdout.strip():
    print("No commits to process.. May be a invalid commit id")
    sys.exit(1)

commits = sorted(set(grep_output.stdout.splitlines()), reverse=True)

sorted_commits=[]
for line in commits:
	sorted_commits.append(line.split(':')[1].split()[0])

print("Commits sorted....")

# Trapping signal SIGINT and SIGTERM
signal.signal(signal.SIGINT, clear_cp)
signal.signal(signal.SIGTERM, clear_cp)

# Applying the commits
for commit in sorted_commits:
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
                    run_command("git add -u")
                    run_command("git cherry-pick --continue")
                    break
                elif user_input == "abort" or user_input == 'a':
                    if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
                        os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
                    run_command(f"git config core.editor 'vi'")
                    run_command("git cherry-pick --abort")
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

# Display a completion message
print("All commits have been processed.")

#Reset editor back to "vim"
if os.path.exists("$PWD/.git/.COMMIT_EDITMSG.swp"):
    os.remove("$PWD/.git/.COMMIT_EDITMSG.swp")
run_command(f"git config core.editor 'vi'") 

# Clean up the temporary files
os.remove(tmpfile)
os.remove(temp_file_path)
os.remove(temp_script_path)

# Untrap the signals by resetting them to default behavior
signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGTERM, signal.SIG_DFL)
