#!/bin/bash

# Define temporary files
tmpfile="/tmp/commit"
tmpfile2="/tmp/commit_1"
sortfile="/tmp/sort"

# IRQ for trapped signal
clear_cp () {
	echo "Processing Interrupt..."
	git cherry-pick --abort
	echo "cherry-pick abort..."
	exit 1
}

# Initialize an array to hold the commit IDs
commits=()

# Read multiple lines of commit IDs into the 'commits' array
echo "Enter the commit IDs (one per line). Press Ctrl+D when done:"
while IFS= read -r line; do
	commits+=("$line")
done 

# Remove temporary files if they exist
[ -e "$tmpfile" ] && rm "$tmpfile"
[ -e "$sortfile" ] && rm "$sortfile"

# Write commit IDs to the temporary file
for commit in "${commits[@]}"; do
	echo "$commit" >> "$tmpfile"
done

# Sort and unique the commit IDs, then prepare the grep commands
cat "$tmpfile" | awk '{print "grep -n " $1 " ~/log"}' > "$tmpfile2"
chmod 755 "$tmpfile2"
bash "$tmpfile2" | sort -ugr | cut -d: -f2 | awk '{print $1}' > "$sortfile"
chmod 755 "$sortfile"
echo "Commits sorted...."

# Execute the sorted commands and process the output
commits=()
while IFS= read -r line; do
	commits+=("$line")
done < "$sortfile"

#trapping signal SIGINT and SIGTERM
trap clear_cp SIGINT SIGTERM

for commit in "${commits[@]}"; do
    	echo "Applying commit $commit ...."
    	git cherry-pick -x "$commit"
    	if [ $? -ne 0 ]; then
	    	echo;echo "Conflict occurred while applying commit $commit. \
			Resolve the conflict and enter 'done' to continue."
        	while true; do
            		read command
            		if [ "$command" == "done" ]; then
                		break
            		else
				eval $command
            		fi
        	done
    	fi
    	echo "Commit $commit successfully applied...."
done

# Display a completion message
echo "All commits have been processed."

# Clean up temporary files
rm "$tmpfile"
rm "$sortfile"

