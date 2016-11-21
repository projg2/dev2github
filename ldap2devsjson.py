#!/usr/bin/env python
# Create devs.json from 'perl_ldap -S gentooGitHubUser' output
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import sys


def main(list_f='devs.txt', devs_json='devs.json'):
    devs = {}
    with open(list_f) as f:
        for l in f:
            if l.startswith('Searching'):
                continue
            elif not l.strip():
                continue
            spl = [x.strip() for x in l.split('->')]
            assert len(spl) == 2
            if spl[1] == 'undefined':
                spl[1] = ''
            devs[spl[0]] = spl[1]

    with open(devs_json, 'w') as devs_f:
        json.dump(devs, devs_f, indent=0, sort_keys=True)

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
