# Poker Server Setup

## Install Poker Mavens
TODO

### Open up Firewall for Poker Mavens
TODO

## Restore config data
TODO

``` shell
C:\Users\Adminsitrator\AppData\Roaming\Poker Mavens
```

## Install Chocolatey

https://chocolatey.org/docs/installation

``` powershell
# install
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# test
choco --version
```

## Install git

https://git-scm.com/download/win

``` powershell
choco install -y git
```

``` powershell
GIT_PATH = %ProgramFiles%\Git
# append the following to PATH
PATH = %GIT_PATH%\bin
```

## Install hugo

https://gohugo.io/getting-started/installing/

``` powershell
choco install -y hugo
```

## Install python

https://www.python.org/downloads/windows/

``` powershell
choco install -y python3
```

Add the following System environment variables in Syste -> Advanced System Settings -> Advanced -> Environment Variables:

``` powershell
PYTHON_PATH = C:\Python38
# append the following to PATH
PATH = ;%PYTHON_PATH%;%PYTHON_PATH%\Scripts
```
You will now have to start a new PowerShell session for these variables to be updated.

## Setup GitHub deploy key (SSH)

``` bash
# run this on a linux box or figure out the equivelent on windows
ssh-keygen -o -a 100 -t ed25519

# put the SSH keys into C:\Users\<username>\.ssh

# copy the public key into the GitHub repo as a deploy key
```

## Clone repo

``` powershell
mkdir git
cd git
git clone git@github.com:nmaludy/urg-poker-leaderboard.git
cd urg-poker-leaderboard
python.exe -m venv venv
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Setup the config

``` powershell
# assuming you're in the urg-poker-leaderboard directory
cp config.example.yaml config.yaml
notepad.exe config.yaml
```

## Setup scheduled task

``` powershell
General:
  user: administrator
  Run whether user is logged in or not
  Configure For: Server 2012 R2

Triggers:
  Schedule:
  Daily @ 8pm
  Repeat every 10 minutes for a duration of 2 hours
  Enabled

Actions:
 Start a program
 Program/script: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
 Add arguments: -ExecutionPolicy Bypass -Command "&{ C:\Users\nmaludy\git\urg-poker-leaderboard\run_windows.ps1 *> C:\Users\nmaludy\git\urg-poker-leaderboard\poker_mavens.log }; exit $LASTEXITCODE"
```

Configure user to have Logon as Batch Job rights:

```powershell
Start -> Control Panel
Administrative Tools -> Local Secirty Policy
Local Policies -> User Rights Assignment
Log on as a batch job
< add user >
```

# Create the site from scratch


``` shell
git clone git@github.com:nmaludy/urg-poker-leaderboard.git
cd urg-poker-leaderboard
hugo new site urg-poker-leaderboard
mv urg-poker-leaderboard/* .
rm -rf urg-poker-leaderboard/
git submodule add https://github.com/pacollins/hugo-future-imperfect-slim themes/hugo-future-imperfect
```

## Setup travis deploy key
https://gist.github.com/qoomon/c57b0dc866221d91704ffef25d41adcf


## python generator script setup

Install python (3.6+) https://www.python.org/downloads/

``` shell
    python3 -m venv venv
source ./venv/Scripts/activate
pip install -r requirements.txt
```

# Adding new scores automatically

``` shell
source ./venv/Scripts/activate
# This will automatically commit and push
python ./poker_mavens.py
```

## Adding new score (manual)

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
