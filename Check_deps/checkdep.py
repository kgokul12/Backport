#!/usr/bin/python3

import os
import sys
import subprocess
import re
import concurrent.futures

# Define a function to check each commit in parallel
def check_commit(cmid):
    short_cmid = cmid[:12]

    # Check for dependencies using `--grep`
    deps_result = subprocess.run(f"git log origin/stable_kernel_6.13 --oneline --grep=\"Fixes: {short_cmid}\"", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    deps_output = deps_result.stdout.strip() or "no deps"
    return f"==>checking {short_cmid}\n{deps_output}"

# function to process commit ids if not given as input 
def Process_upstream(up_cmids,count):
    log_out = subprocess.run(f"git log -{count} ", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    lines = [line for line in log_out.stdout.splitlines()]

    pattern = rf"\b{re.escape('commit')}\s+(\w+)\s+{re.escape('upstream')}\b"

    for line in lines:
        if re.search(pattern, line):
            up_cmids.append(line.strip().split()[1])

#Function to process commit ids given as input
def getlist(input_list):
    print("Enter a value (or type 'done' to finish): ")
    while True:
        user_input = input()
        if user_input.lower() == 'done':
             break
        input_list.append(user_input)

#--MAIN--
# check the arguments
if len(sys.argv) < 2:
    print("Enter the count(inside Linux_Backport repo) or -l(to add a list of commit ids) to check the deps")
    sys.exit(0)

up_cmids = []
count=0

try:
    ret_val = int(sys.argv[1])
    count = sys.argv[1]
except ValueError:
    if sys.argv[1] == "-l":
        getlist(up_cmids)
    else :
        print("Invalid input")
        sys.exit(1)

if count != 0 :
    Process_upstream(up_cmids,count)

print(up_cmids)
# Use a ThreadPoolExecutor for parallel processing
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(check_commit, up_cmids))

# Print all results
for result in results:
    print(result)
