if [ $# -eq 0 ];then
	echo -e  "To skip copying log use\n\t$ ./commit.sh -i\n\t*only if you copied the log filein /tmp/log" 
	echo
fi
echo;echo "checking commits in branch -->`git branch --show-current`";echo
echo "Enter all the commits " 
if [ $# -eq 0 ];then
	echo "Wait, It's logging...."
	git log > /tmp/log
	git log --pretty=oneline > /tmp/1_log
fi
echo -e "\n ######################################### \n"

x=0    #Available commits count
y=0    #Not Available commits count
z=0    #May be as Upstream

# Read multiple lines of commit IDs into the 'commits' array
commits=()
echo "Now, Enter the commit IDs (one per line). Press Ctrl+D when done:"
while IFS= read -r line; do
        commits+=("$line")
done

for cmid in "${commits[@]}";
do
    cat /tmp/1_log | grep -q $cmid
    if [ $? -eq 0 ];
    then
	    ((x++))
	    echo "`git show $cmid |grep $cmid`   Available"
    else 
	    cat /tmp/log | grep $cmid
	    if [ $? -eq 0 ];
	    then 
		    ((z++))
		    echo "commit $cmid   Available like this" 
	    else
		    ((y++))
		    echo "commit $cmid   Not Available"
	    fi
    fi
    count=$((count-1))
done
echo -e "\n ######################################### \n"
echo -e "\tTotally -($x)- commits Available directly -($z)- may be as upstream and -($y)- commits Not Available\n" 
echo -e "\tCheck these $z commits and decide"
