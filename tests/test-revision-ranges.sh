#! /bin/bash

SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`

VERBODE=INFO
export PUBLIC_KEYS_PATH=/public-keys

echo "Creating keys"
$SCRIPTPATH/gpg-create.sh

echo "Create Git repo"
$SCRIPTPATH/git-create.sh


git checkout branch-missing-signature
/checker/checker.py -l$VERBODE --git-dir .git --public-keys /public-keys
if [ $? -eq 0 ]; then
    echo "*** Failed - signature verification should fail"
    exit -1
fi

git checkout master
/checker/checker.py -l$VERBODE --git-dir .git --public-keys /public-keys
if [ $? -ne 0 ]; then
    echo "*** Failed - signature verification should be succesful"
    exit -1
fi


echo "All tests succesful!"
