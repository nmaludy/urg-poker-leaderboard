echo "Deleting old publication"
rm -r -force public
mkdir public
git worktree prune
rm -r -force .git\worktrees\public

echo "Checking out gh-pages branch into public"
git worktree add -B gh-pages public origin/gh-pages

echo "Removing existing files"
ls public\* | rm -r

echo "Generating site"
hugo

echo "Updating gh-pages branch"
cd public
git add --all
git commit -m "Publishing to gh-pages (publish.sh)"
cd ..

#echo "Pushing to github"
#git push --all