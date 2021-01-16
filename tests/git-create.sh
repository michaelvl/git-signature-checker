#! /bin/bash

set -e

function do_commit {
    msg=$1
    user=$2
    echo "Commit $msg" > README.txt
    git add README.txt
    git commit -S$user -m "$msg"
}

function do_unsigned_commit {
    msg=$1
    user=$2
    echo "Commit (unsigned) $msg" > README.txt
    git add README.txt
    git commit -m "Unsigned $msg"
}


git init

git config --global user.email "you@example.com"
git config --global user.name "Your Name"
do_commit "Initial commit" "james@example.com"

git checkout -b branch-missing-signature
do_unsigned_commit "Commit b1"
do_commit "Commit b2"      "william@example.com"
do_commit "Commit b3"      "william@example.com"

git checkout master
do_commit "Commit 2"       "william@example.com"
do_commit "Commit 3"       "frank@example.com"

echo "Verbose Git graph"
git log --abbrev-commit --graph --decorate --show-signature master branch-missing-signature
echo "Git graph"
git log --abbrev-commit --graph --decorate master branch-missing-signature
