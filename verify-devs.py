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

    for dev, ghdev in devs.items():
        if not ghdev:
            continue
        try:
            gh.get_user(ghdev)
        except github.UnknownObjectException:
            print('Dev not found: %s (%s)' % (ghdev, dev))

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
