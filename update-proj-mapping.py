#!/usr/bin/env python
# Write project mapping from e-mails to GitHub
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os.path
import sys

import github
import lxml.etree


def main(projects_xml='projects.xml', proj_map_json='proj-map.json'):
    with open(os.path.expanduser('~/.github-token')) as f:
        gh = github.Github(f.read().strip())

    projs_x = lxml.etree.parse(projects_xml)
    projs = {}
    for p in projs_x.getroot():
        projs[p.findtext('email').split('@')[0].lower()] = p
        projs[p.findtext('name').split('@')[0].lower()] = p
        projs[p.findtext('url').split(':')[2].lower()] = p

    proj_map = {}
    rem_projs = set(p for p in projs_x.getroot())

    gorg = gh.get_organization('gentoo')
    for t in gorg.get_teams():
        p = projs.get(t.name.lower())
        if p is not None:
            print('%s <-> %s' % (t.name, p))
            proj_map[p.findtext('email').lower()] = 'gentoo/' + t.name
            rem_projs.remove(p)
        else:
            print('%s <-> ?' % (t.name,))

    for p in rem_projs:
        print('MISSING PROJECT: %s' % p.findtext('email'))

    with open(proj_map_json, 'w') as f:
        json.dump(proj_map, f, indent=0, sort_keys=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
