#!/usr/bin/env python
# Sync projects to GitHub
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import os.path
import sys

import github
import lxml.etree

def add_members(members, p, xmltree):
    members += [m.findtext('email').split('@')[0].lower() for m in p.findall('member')]

    for subp in p.findall('subproject'):
        if subp.get('inherit-members') == '1':
            subp_email = subp.get('ref')
            for op in xmltree:
                if op.findtext('email') == subp_email:
                    add_members(members, op, xmltree)


def main(devs_json='devs.json', projects_xml='projects.xml'):
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)

    with open(os.path.expanduser('~/.github-token')) as f:
        gh = github.Github(f.read().strip())

    projs_x = lxml.etree.parse(projects_xml)
    projs = {}
    for p in projs_x.getroot():
        projs[p.findtext('email').split('@')[0].lower()] = p
        projs[p.findtext('name').split('@')[0].lower()] = p
        projs[p.findtext('url').split(':')[2].lower()] = p

    rev_devs = {v: k.lower() for k, v in devs.items()}

    for t in gh.get_organization('gentoo').get_teams():
        p = projs.get(t.name.lower())
        if p is not None:
            print('%s <-> %s' % (t.name, p))
            members = []
            add_members(members, p, projs_x.getroot())
            gh_members = []
            for m in t.get_members():
                if m.login in rev_devs:
                    gh_members.append(rev_devs[m.login])
                    if rev_devs[m.login] not in members:
                        print('REMOVE %s' % m)
                        t.remove_from_members(m)
            for m in members:
                if devs.get(m) and m not in gh_members:
                    u = gh.get_user(devs[m])
                    print('ADD %s' % u)
                    t.add_to_members(u)
        else:
            print('%s <-> ?' % (t.name,))

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))

