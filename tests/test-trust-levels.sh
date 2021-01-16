#! /bin/bash

SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`

VERBODE=INFO
export PUBLIC_KEYS_PATH=/public-keys
export GNUPGHOME=/tmp

echo "Creating keys"
$SCRIPTPATH/gpg-create.sh

echo "Create Git repo"
$SCRIPTPATH/git-create.sh

# Ignore keyring created by gpg-create.sh
unset GNUPGHOME

/checker/checker.py -l$VERBODE --git-dir .git --public-keys /public-keys --minimum-trust ULTIMATE
if [ $? -eq 0 ]; then
    echo "*** Failed - signature verification should fail"
    exit -1
fi

/checker/checker.py -l$VERBODE --git-dir .git --public-keys /public-keys
if [ $? -ne 0 ]; then
    echo "*** Failed - signature verification should be succesful"
    exit -1
fi


echo "All tests succesful!"
