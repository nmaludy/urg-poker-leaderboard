# Setup

``` shell
git clone git@github.com:nmaludy/urg-poker-leaderboard.git
cd urg-poker-leaderboard
hugo new site urg-poker-leaderboard
mv urg-poker-leaderboard/* .
rm -rf urg-poker-leaderboard/
git submodule add https://github.com/pacollins/hugo-future-imperfect-slim themes/hugo-future-imperfect
```

# Adding new score

``` shell
mkdir content/scores/
export YEAR=$(date +%Y)
export YEAR_MONTH=$(date +%Y-%m)
export TODAY=$(date +%Y-%m-%d)
cat << EOF > "content/scores/${TODAY}.md"
+++
author = "URG Poker Bot"
author_url = "urgpoker.com"
categories = ["${YEAR}", "$YEAR_MONTH"]
date = "${TODAY}"
title = "Scores for ${TODAY}"
type = "post"
+++

| Place | User | Score |
|-------|------|-------|
| 1 | Larry | 800 |
| 2 | Nick | 200 |
| 3 | Jeff | 400 |
EOF

```

# Deploy

https://gohugo.io/hosting-and-deployment/hosting-on-github/#deployment-of-project-pages-from-your-gh-pages-branch

### Do these once on the repo (already done here)

``` shell
./bin/setup_ghpages_branch.sh
```

### Do these every time you want to deploy

``` shell
./bin/publish_to_ghpages.sh
```
