#!/usr/bin/env python
# Sync developers team on GitHub (invite or remove)
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

    members = set(m.login for m in t.get_members())

    for dev, ghdev in devs.items():
        if not ghdev:
            continue
        if ghdev not in members:
            print('INVITE %s (%s)' % (ghdev, dev))
            t.add_membership(gh.get_user(ghdev))
        else:
            members.remove(ghdev)

    for m in members:
        print('REMOVE %s' % m)
        t.remove_from_members(gh.get_user(m))

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))