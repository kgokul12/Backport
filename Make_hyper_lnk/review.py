import sys
import subprocess

# Check if the count is provided as a command-line argument
if len(sys.argv) < 2:
    print("Enter the number of commits you want to see:")
    sys.exit(1)

# Get the number of commits from the command-line argument
count = int(sys.argv[1])

# Run the git log command to get the specified number of commits
result = subprocess.run(
    ["git", "log", "--pretty=oneline", f"-n{count}"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,  # Treat output as text
    check=True  # Raise an exception if the command fails
)

# Print the full output of the git log command
print(result.stdout)

# Initialize an empty list to store commit IDs
bpcmids= []
names=[]

# Split the output into individual commits
list_commits = result.stdout.strip().split('\n')
for commit in list_commits:
    commit = commit .strip().split(' ')
    bpcmids.append(commit[0])
    names.append(' '.join(commit[1:]))

html_content=""
i=1

for bpcmid, name  in zip(bpcmids[::-1], names[::-1]):
    #links
    bplink = "https://github.com/AMDEPYC/Linux_Backport/commit/"
    uplink = "https://github.com/torvalds/linux/commit/"
    
    try:
        result=subprocess.run(
                ["git","show",f"{bpcmid}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True
                )
    # Filter the output with `grep` for 'upstream'
        grep_result = subprocess.run(
                ["grep", "upstream"],
                input=result.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True
                )
        #file.write(result.stdout)
        upcmid = grep_result.stdout.strip().split(' ')
        upcmid = upcmid[1]
        print(f"{upcmid}")
    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e.stderr}")
    
   # Generate HTML content with hyperlinks
    name = f"\n{i}. {name}"
    bplink += bpcmid
    uplink += upcmid
    bpcmid = f"Backport commit id : <a href=\"{bplink}\">{bpcmid[:14]}</a><br>\n"
    upcmid = f"Upstream commit id : <a href=\"{uplink}\">{upcmid[:14]}</a><br>\n\n"
    html_content += "<html><body>\n"
    html_content +=f"<h4>{name}</h4>\n <ul><li>{bpcmid}</li> <li>{upcmid}</li></ul>\n"
    html_content += "</body></html>"
    i+=1

# Write the HTML content to a file
with open("/home/amd/commits.html", "w") as file:
    file.write(html_content)

print("HTML file with hyperlinks created.")






