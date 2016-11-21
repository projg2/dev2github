#!/usr/bin/env python
# Verify GitHub usernames in devs.json
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import os.path
import sys

import github


def main(devs_json='devs.json'):
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)

    with open(os.path.expanduser('~/.github-token')) as f:
        gh = github.Github(f.read().strip())
    
    for t in gh.get_organization('gentoo').get_teams():
        if t.name == 'developers':
            break
    else:
        raise RuntimeError('Unable to find developers team')

    members = frozenset(m.login for m in t.get_members())

    for dev, ghdev in devs.items():
        if not ghdev:
            continue
        if ghdev not in members:
            print('Dev not found in developers team: %s (%s)' % (ghdev, dev))

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
