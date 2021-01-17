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

def get_pub_keys(args):
    if not args.public_keys:
        return []
    path = args.public_keys
    fobjs = [os.path.join(path, o) for o in os.listdir(path)]
    pubk = [f for f in fobjs if os.path.isfile(f)]
    logging.info("Found {} public key(s) in '{}'".format(len(pubk), path))
    return pubk

def get_fingerprints(pubk_files):
    fps = []
    for f in pubk_files:
        cmd = ['gpg', '--import', '--with-colons', '--with-fingerprint', '--import-options', 'import-show', f]
        logging.debug("Running: '{}'".format(cmd))
        ret = subprocess.run(cmd, capture_output=True)
        info = ret.stdout.split(b'\n')
        for ln in info:
            fields = ln.split(b':')
            if fields[0] == b'fpr':
                fps.append(fields[9])
    logging.info('Found {} fingerprints:'.format(len(fps)))
    for fp in fps:
        logging.info('  {}'.format(fp))
    return fps

def get_git_commits(args):
    cmd = ['git', '--git-dir', args.git_dir, 'log', '--format=format:%H', '--no-merges']
    if args.revision_range:
        cmd.append(args.revision_range)
    logging.debug("Running: '{}'".format(cmd))
    commits = subprocess.check_output(cmd).split(b'\n')
    logging.info('Found {} commits. Most recent {}, oldest {}'.format(len(commits), commits[0], commits[-1]))
    return commits

def gpg_trust_txt2lvl(trust):
    for idx,l in enumerate(['UNKNOWN', 'MARGINALLY', 'FULLY', 'ULTIMATE']):
        if trust.upper()==l:
            return idx
    return 0

def parse_git_verify_commit_output(out):
    stat = {}
    goodsig = re.compile(b'\[GNUPG:\] GOODSIG [0-9A-Z]+\s+([\w\s]+\w)\s+(.*)')
    goodsig_email = re.compile(b'.*\<([\w\@\.]+)\>')
    validsig = re.compile(b'\[GNUPG:\] VALIDSIG ([0-9A-Z]+)\s.*')
    trust = re.compile(b'\[GNUPG:\] TRUST_(\w+)\s.*')
    for ln in out.split(b'\n'):
        logging.debug("Parsing '{}'".format(ln))
        r = goodsig.match(ln)
        if r:
            stat['by'] = r.group(1)
            r = goodsig_email.match(r.group(2))
            if r:
                stat['email'] = r.group(1)
        r = validsig.match(ln)
        if r:
            stat['validsig'] = True
            stat['fingerprint'] = r.group(1)
        r = trust.match(ln)
        if r:
            stat['trust'] = r.group(1).decode('utf-8')
            stat['trust_level'] = gpg_trust_txt2lvl(stat['trust'])
    logging.debug('Parsed result: {}'.format(stat))
    return stat

def validate_signature(args, commit, verify_stat, fingerprints):
    if not verify_stat['validsig']:
        logging.error('Not a valid signature')
    elif not verify_stat['trust']:
        logging.error('No trust level found')
    elif gpg_trust_txt2lvl(args.minimum_trust)>verify_stat['trust_level']:
        logging.error('Too low trust level {}<{}'.format(verify_stat['trust'], args.minimum_trust))
    elif not verify_stat['fingerprint']:
        logging.error('No fingerprint found')
    elif fingerprints and verify_stat['fingerprint'] not in fingerprints:
        # Empty fingerprint list means use whatever our gpg keyring have
        logging.error('Fingerprint found, but does not match trusted set')
    else:
        return True
    return False

def check_git_signatures(args, commits, fingerprints):
    for commit in commits:
        cmd = ['git', '--git-dir', args.git_dir, 'verify-commit', '--raw', commit]
        env = os.environ
        if args.keyring:
            env['GNUPGHOME'] = args.keyring
        logging.debug("Running: '{}', env={}".format(cmd, env))
        ret = subprocess.run(cmd, env=env, capture_output=True)
        logging.debug('Return status: {}'.format(ret))
        if ret.returncode != 0:
            logging.error('FAILURE: Commit {} could not be verified'.format(commit))
            sys.exit(-1)
        verify_stat = parse_git_verify_commit_output(ret.stderr)
        if validate_signature(args, commit, verify_stat, fingerprints):
            if 'email' in verify_stat:
                by = verify_stat['email']
            else:
                by = verify_stat['by']
            logging.info('OK: Commit {}: {} (trust:{})'.format(commit, by, verify_stat['trust']))
        else:
            logging.error('FAILURE: Commit {} could not be verified'.format(commit))
            sys.exit(-1)
    logging.info('All {} commit signatures validated (trust level {})'.format(len(commits), args. minimum_trust))

def main():
    parser = argparse.ArgumentParser(description='Git GPG signature checker')
    parser.add_argument('-l', dest='log_level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the log level')

    parser.add_argument('--git-dir', required=True)
    parser.add_argument('--public-keys')
    parser.add_argument('--keyring')
    parser.add_argument('--revision-range', default=None)
    parser.add_argument('--minimum-trust', default='UNKNOWN')

    args = parser.parse_args()
    logging.getLogger('').setLevel(getattr(logging, args.log_level))
    
    versions = get_tools_versions()
    pub_keys = get_pub_keys(args)
    if len(pub_keys)==0:
        logging.warning('No public keys found')
    fingerprints = get_fingerprints(pub_keys)
    commits = get_git_commits(args)
    check_git_signatures(args, commits, fingerprints)

if __name__ == "__main__":
   sys.exit(main())
