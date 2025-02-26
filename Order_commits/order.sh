#get input commits
read -p "Enter the no. of commit you want in order: " count
rm -r /tmp/unordered_patch ../tmp_$dir_name

# old patch ctreation
echo "#Creating unordered_patch in (\/tmp\/unordered_patch)..."
git format-patch -q -p$count -o /tmp/unordered_patch

# temp dir to process commits
dir_name=$(basename $(pwd))
cp -rf ../$dir_name ../tmp_$dir_name
echo "#creating a tmp dir - tmp_$dir_name"
cd ../tmp_$dir_name
pwd
acp -r $count

#setting up tmp_dir
echo "#Setting up- tmp_$dir_name"
rm -rf .git
git init -q
git config init.defaultBranch main
git add .
git commit -q -m "inital commit"
git branch -c test
git am -q /tmp/unordered_patch/*

# take upstreams commits
git log |grep "commit .* upstream$" | awk '{print $2}' > /tmp/ord1

#check order of upstream commits
echo "#checking order of upstream commits...."
acp -cl
acp -a < /tmp/ord1 1>/dev/null
acp -l > /tmp/ordered_upstream
echo "#ordered upstream forwarded to /tmp/ordered_upstream"

#finding backport id in order of upstream
cat /tmp/ordered_upstream | awk '{print $1}' | cut -d: -f2 > /tmp/or2 
sed -i '$d' /tmp/or2 && sed -i '$d' /tmp/or2
sed -i 's/^/git log --oneline --grep="commit /' /tmp/or2
sed -i 's/$/ upstream"/' /tmp/or2 

echo "taking backport ids..."
rm /tmp/ordered_bps

echo "git cherry-pick " > /tmp/ordered_bps
chmod +x /tmp/or2 /tmp/ordered_bps
/tmp/or2 > /tmp/or3 
cat /tmp/or3 | awk '{print $1}' >> /tmp/ordered_bps
sed -i 's/$/ \\/' /tmp/ordered_bps

git checkout test 
echo "#Applying patches..."
/tmp/ordered_bps
while [ $? -ne 0 ];do 
    read -p "\n\n###conflict occured, resolve and enter \"done\"\n" opt
    while [ $opt -ne "done" ];do
	read -p "Invalid option" opt
    done
    git add -u; git cherry-pick --continue
done

git format-patch -q -p$count -o ~/ordered_patced

cd ../
rm -rf tmp_$dir_name
acp -cl
echo "#ordered patches available in ===>  \"\~\/ordered_patced\""

