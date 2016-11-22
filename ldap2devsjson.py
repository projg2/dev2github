#!/usr/bin/env python
# Create devs.json from LDIF
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import sys


def main(list_f='devs.ldif', devs_json='devs.json'):
    devs = {}
    with open(list_f) as f:
        ldif_data = f.read()

    for block in ldif_data.split('\n\n'):
        if not block.strip():
            continue
        mails = set()
        ghuser = ''
        for l in block.splitlines():
            k, v = l.split(': ')
            if k == 'uid':
                mails.add(v + '@gentoo.org')
            elif k == 'mail':
                assert '@' in v
                mails.add(v)
            elif k == 'gentooGitHubUser':
                ghuser = v
        assert mails
        for m in mails:
           devs[m] = ghuser

    with open(devs_json, 'w') as devs_f:
        json.dump(devs, devs_f, indent=0, sort_keys=True)

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
