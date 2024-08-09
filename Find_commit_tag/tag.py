#!/bin/bash

# List of commit IDs (replace these with your actual commit IDs)
commits=("39621c5808f5dda75d03dc4b2d4d2b13a5a1c34b")

# Directory containing the Linux kernel source code
kernel_dir="/home/amd/Priya/Linux_Backport/"

# Change to the kernel source directory
#cd /home/amd/Priya/Linux_Backport 


# Function to find the kernel version for a commit
find_kernel_version() {
    local commit_id=$1
    local versions
    versions=$(git tag --contains "$commit_id" 2>/dev/null)
    
    if [[ -n "$versions" ]]; then
        echo "Commit $commit_id was introduced in kernel version(s):"
        echo "$versions"
    else
        echo "Commit $commit_id was not found in any tagged kernel version."
    fi
}

# Iterate over the list of commits and find their kernel versions
for commit in "${commits[@]}"; do
    find_kernel_version "$commit"
done

