#!/usr/bin/env python
# Update devs.json using plain text list (i.e. add new devs)
# (c) 2016 Michał Górny, 2-clause BSD licensed

import errno
import json
import os
import sys


def main(list_f='devs.txt', devs_json='devs.json'):
    try:
        with open(devs_json) as devs_f:
            devs = json.load(devs_f)
    except OSError as e:
        if e.errno == errno.ENOENT:
            devs = {}
        else:
            raise

    with open(list_f) as f:
        for dev in f:
            dev = dev.strip()
            if not dev:
                continue
            if dev not in devs:
                devs[dev] = ''

    new_devs_json = devs_json + '.new'
    with open(new_devs_json, 'w') as devs_f:
        json.dump(devs, devs_f, indent=0, sort_keys=True)
    os.rename(new_devs_json, devs_json)

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
