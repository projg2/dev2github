#!/usr/bin/env python
# generate heliosvoting-friendly voters list from project members

import argparse
import json
import sys


def main(argv):
    argp = argparse.ArgumentParser()
    argp.add_argument('--json',
                      default='projects.json',
                      type=argparse.FileType('r'),
                      help='projects.json file')
    argp.add_argument('project',
                      help='project name')
    args = argp.parse_args(argv)

    if '@' not in args.project:
        args.project += '@gentoo.org'

    j = json.load(args.json)
    for p in j.values():
        if p['email'] == args.project:
            break
    else:
        raise RuntimeError('project not found')

    for m in p['members']:
        print(f'{m["email"].split("@")[0]},{m["email"]},{m["name"]}')


if __name__ == '__main__':
    main(sys.argv[1:])
