#! /bin/bash

set -e

PUBKEYS=${PUBLIC_KEYS_PATH:-/public-keys}


function create_key {
    name=$1
    email=$2
    comment=$3
    cat >foo <<EOF
     %echo Generating a basic OpenPGP key for $name
     Key-Type: DSA
     Key-Length: 1024
     Subkey-Type: ELG-E
     Subkey-Length: 1024
     Name-Real: $name
EOF
    if [ ! -z $comment ]; then
        echo "Name-Comment: $comment" >> foo
    fi
    cat >>foo <<EOF
     Name-Email: $email
     Expire-Date: 0
     #Passphrase: ""
     %no-protection
     # Do a commit here, so that we can later print "done" :-)
     %commit
     %echo done
EOF

    gpg --batch --generate-key foo
}

create_key "James"   "james@example.com"
create_key "Frank"   "frank@example.com"   "A personal key for Frank"
create_key "William" "william@example.com"

gpg --list-keys

echo "Exporting public keys to $PUBKEYS"
mkdir -p $PUBKEYS
gpg --armor --export james@example.com > $PUBKEYS/james-pub-key.asc
gpg --armor --export frank@example.com > $PUBKEYS/frank-pub-key.asc
gpg --armor --export william@example.com > $PUBKEYS/william-pub-key.asc
