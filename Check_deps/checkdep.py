#!/usr/bin/python3

import os
import sys
import subprocess
import re
import concurrent.futures

# Define a function to check each commit in parallel
def check_commit(cmid):
    short_cmid = cmid[:12]
#    if short_cmid not in stable_log:
#        return f"commit {short_cmid} not available"

    # Check for dependencies using `--grep`
    deps_result = subprocess.run(f"git log origin/stable_kernel_6.11 --oneline --grep {short_cmid}", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    deps_output = deps_result.stdout.strip() or "no deps"
    return f"==>checking {short_cmid}\n{deps_output}"

# check the arguments
if len(sys.argv) < 2:
    print("Enter the count or commit id to check the deps")
    sys.exit(0)

try:
    ret_val = int(sys.argv[1])
    count = sys.argv[1]
except ValueError:
    print(check_commit(sys.argv[1]))
    sys.exit(0)

log_out = subprocess.run(f"git log -{count} ", stdout=subprocess.PIPE, shell=True, universal_newlines=True)
lines = [line for line in log_out.stdout.splitlines()]

pattern = rf"\b{re.escape('commit')}\s+(\w+)\s+{re.escape('upstream')}\b"
up_cmids = []

for line in lines:
    if re.search(pattern, line):
        up_cmids.append(line.strip().split()[1])
#print([x for x in up_cmids])

#result = subprocess.run(f"git log origin/stable_kernel_6.11 --oneline", stdout=subprocess.PIPE, shell=True, universal_newlines=True, errors='ignore')
#stable_log = result.stdout.splitlines()

# Use a ThreadPoolExecutor for parallel processing
with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(check_commit, up_cmids))

# Print all results
for result in results:
    print(result)

