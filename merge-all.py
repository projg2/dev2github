#!/usr/bin/env python
# Merge developers & proxied maintainers JSON
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import os.path
import sys


def main(devs_json='devs.json', proxied_maints_json='proxied-maints.json', all_json='all.json'):
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)
    with open(proxied_maints_json) as pm_f:
        maints = json.load(pm_f)

    devs.update(maints)
    with open(all_json, 'w') as all_f:
        json.dump(devs, all_f)

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
