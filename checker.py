#!/usr/bin/env python3

import os, sys
import logging
import argparse
import subprocess
import re

def get_tools_versions():
    versions = {}
    cmd = ['gpg', '--version']
    logging.debug("Running: '{}'".format(cmd))
    info = subprocess.check_output(cmd).split(b'\n')
    v = info[0].decode("utf-8")
    logging.debug("GPG version string: '{}'".format(v))
    m = re.match('.* (\d+\.\d+\.\d+)', v)
    if m:
        versions['gpg'] = m.group(1)

    cmd = ['git', '--version']
    logging.debug("Running: '{}'".format(cmd))
    info = subprocess.check_output(cmd).split(b'\n')
    v = info[0].decode("utf-8")
    logging.debug("Git version string: '{}'".format(v))
    m = re.match('.* (\d+\.\d+\.\d+)', v)
    if m:
        versions['git'] = m.group(1)

    logging.info('Tools versions: {}'.format(versions))
    return versions

def get_pub_keys(path):
    fobjs = [os.path.join(path, o) for o in os.listdir(path)]
    pubk = [f for f in fobjs if os.path.isfile(f)]
    logging.info("Found {} public key(s) in '{}'".format(len(pubk), path))
    return pubk

def get_fingerprints(pubk_files):
    fps = []
    for f in pubk_files:
        #cmd = ['gpg', '--with-colons', '--with-fingerprint', '--import-options', 'show-only', f]
        cmd = ['gpg', '--import', '--with-colons', '--with-fingerprint', '--import-options', 'import-show', f]
        logging.debug("Running: '{}'".format(cmd))
        info = subprocess.check_output(cmd).split(b'\n')
        for ln in info:
            fields = ln.split(b':')
            if fields[0] == b'fpr':
                fps.append(fields[9])
    logging.info('Found {} fingerprints:'.format(len(fps)))
    for fp in fps:
        logging.info('  {}'.format(fp))
    return fps

def get_git_commits(git_dir):
    cmd = ['git', '--git-dir', git_dir, 'log', '--format=format:%H', '--no-merges']
    logging.debug("Running: '{}'".format(cmd))
    commits = subprocess.check_output(cmd).split(b'\n')
    logging.info('Found {} commits. Most recent {}, oldest {}'.format(len(commits), commits[0], commits[-1]))
    return commits

def check_signatures(commits, fingerprints, git_dir):
    for hash in commits:
        cmd = ['git', '--git-dir', git_dir, 'verify-commit', '--raw', hash]
        logging.debug("Running: '{}'".format(cmd))
        gpg_out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).split(b'\n')
        ok = b'[GNUPG:] GOODSIG '
        validsig = b'[GNUPG:] VALIDSIG '
        ok_by = None
        validsig_fp = None
        for ln in gpg_out:
            if ln.startswith(ok):
                ok_by = ln
            if ln.startswith(validsig):
                fp = ln[len(validsig):len(validsig)+40]
                logging.debug('Validsig: {}'.format(fp))
                if fp in fingerprints:
                    validsig_fp = ln
        if ok_by and validsig_fp:
            logging.info('OK: Commit {}: {}'.format(hash, ok_by[len(ok):].decode("utf-8")))
        else:
            raise Exception('FAILURE: Commit {} could not be verified'.format(hash))
    logging.info('All {} commit signatures validated'.format(len(commits)))

def main():
    parser = argparse.ArgumentParser(description='Git GPG signature checker')
    parser.add_argument('-l', dest='log_level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the log level')

    parser.add_argument('--git-dir', required=True)
    parser.add_argument('--public-keys', required=True)



    args = parser.parse_args()
    logging.getLogger('').setLevel(getattr(logging, args.log_level))

    
    versions = get_tools_versions()
    pub_keys = get_pub_keys(args.public_keys)
    if len(pub_keys)==0:
        raise Exception('Needs at least one public key to check signatures against')
    fingerprints = get_fingerprints(pub_keys)
    commits = get_git_commits(args.git_dir)
    check_signatures(commits, fingerprints, args.git_dir)

if __name__ == "__main__":
   sys.exit(main())
