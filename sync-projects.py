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
    members += [m.findtext('email').lower() for m in p.findall('member')]

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
    rem_projs = set(p for p in projs_x.getroot())

    gh_users_cache = {}
    def gh_get_user(x):
        if not x in gh_users_cache:
            gh_users_cache[x] = gh.get_user(x)
        return gh_users_cache[x]

    gorg = gh.get_organization('gentoo')

    for t in gorg.get_teams():
        p = projs.get(t.name.lower())
        if p is not None:
            print('%s <-> %s' % (t.name, p))
            rem_projs.remove(p)
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
                    u = gh_get_user(devs[m])
                    print('ADD %s' % u)
                    t.add_to_members(u)

            # empty now? remove it
            if not list(t.get_members()):
                if not list(t.get_repos()):
                    print('DELETE TEAM')
                    t.delete()
                else:
                    print('EMPTY TEAM WITH REPOS')
        else:
            print('%s <-> ?' % (t.name,))

    for p in rem_projs:
        names = [
            p.findtext('email').split('@')[0],
            p.findtext('name').lower(),
            p.findtext('name'),
            p.findtext('url').split(':')[2].lower(),
            p.findtext('url').split(':')[2]
        ]
        seen = {}
        names = [seen.setdefault(x, x) for x in names if x not in seen]
        desc = p.findtext('description')
        members = []
        add_members(members, p, projs_x.getroot())

        if not members and not p.findall('subproject'):
            print('WARN: %s project has no developers!' % names[0])
            continue
        gh_members = [devs[m] for m in members if devs.get(m)]
        if not gh_members:
            continue

        print('== NEW PROJECT ==')
        print('Name:')
        for i, n in enumerate(names):
            print('%d) %s' % (i+1, n))
        print('Desc: %s' % desc)
        print('Members: %s' % members)
        print('GitHub Members: %s' % gh_members)
        while True:
            resp = input('Proceed? [Y/n/1..%d]' % len(names))
            if resp.lower() in ['', 'y', 'n'] + [str(x) for x in range(1, len(names)+1)]:
                break
            print('Unrecognized reply: %s' % resp)
        if resp.lower() == 'n':
            continue
        if resp.lower() in ('', 'y'):
            resp = '1'
        name = names[int(resp)-1]

        print('CREATE TEAM %s' % name)
        t = gorg.create_team(name, description=desc, privacy='closed')
        for m in gh_members:
            u = gh_get_user(m)
            print('ADD %s' % u)
            t.add_membership(u)

    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
