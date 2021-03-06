#!/bin/sh
# https://gohugo.io/hosting-and-deployment/hosting-on-github/#deployment-of-project-pages-from-your-gh-pages-branch

if [ "`git status -s`" ]
then
  echo "The working directory is dirty. Please commit any pending changes."
  echo "$(git status -s)"
  exit 1;
fi

if [ -n "$TRAVIS_BUILD" ]
then
    git remote add origin git@github.com:nmaludy/urg-poker-leaderboard.git
    git config user.email "administrator@urgpoker.com"
    git config user.name "URG Poker Bot"
fi

echo "Deleting old publication"
rm -rf public
mkdir public
git worktree prune
rm -rf .git/worktrees/public/

echo "Checking out gh-pages branch into public"
git worktree add -B gh-pages public origin/gh-pages

echo "Removing existing files"
rm -rf public/*

echo "Generating site"
hugo

echo "Updating gh-pages branch"
export TODAY=$(date +%Y-%m-%d)
cd public && git add --all && git commit -m "Publishing to gh-pages (publish.sh) - $TODAY"

echo "Pushing to github"
git push origin gh-pages
