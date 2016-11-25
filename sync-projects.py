#!/usr/bin/env python
# Sync projects to GitHub
# (c) 2016 Michał Górny, 2-clause BSD licensed

import collections
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


def main(devs_json='devs.json', projects_xml='projects.xml', proj_map_json='proj-map.json'):
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

    gh_devs = set(devs.values())
    rem_projs = set(p for p in projs_x.getroot())

    gh_users_cache = {}
    def gh_users_to_login(it):
        for u in it:
            gh_users_cache.setdefault(u.login, u)
            yield u.login
    def gh_get_user(x):
        if not x in gh_users_cache:
            gh_users_cache[x] = gh.get_user(x)
        return gh_users_cache[x]

    gorg = gh.get_organization('gentoo')
    owners = set(gh_users_to_login(gorg.get_members(role='admin')))

    proj_map = {}
    for t in gorg.get_teams():
        p = projs.get(t.name.lower())
        if p is not None:
            print('%s <-> %s' % (t.name, p))
            proj_map[p.findtext('email').lower()] = 'gentoo/' + t.name
            rem_projs.remove(p)
            # members = all project members by e-mail
            members = []
            add_members(members, p, projs_x.getroot())
            # gh_members = all project members mapped to github logins
            gh_members = set(devs[x] for x in members if devs[x])

            # team_members = all gh team members, as github.User
            team_members = set(gh_users_to_login(t.get_members()))
            # team_maints = gh team maintainers, as github.User
            team_maints = set(gh_users_to_login(t.get_members(role='maintainer')))

            # owners can't be maints, so assume they are promoted
            team_maints |= team_members & owners

            # remove extraneous gh team members that do have dev acct
            # (i.e. most likely left the team)
            extra_gh_members = team_members - gh_members
            for m in extra_gh_members:
                if m in gh_devs:
                    print('REMOVE %s' % m)
                    t.remove_from_members(gh_get_user(m))
                    team_members.discard(m)

            # promote devs on the team to maintainers
            non_promoted_members = team_members - team_maints
            for m in non_promoted_members:
                if m in gh_devs:
                    print('PROMOTE %s' % m)
                    t.add_membership(gh_get_user(m), role='maintainer')

            # add new devs to the team
            extra_devs = gh_members - team_members
            for m in extra_devs:
                print('ADD %s' % m)
                if m in owners:
                    # owner can't be maintainer
                    t.add_membership(gh_get_user(m))
                else:
                    t.add_membership(gh_get_user(m), role='maintainer')
                team_members.add(m)

            # empty now? remove it
            if not team_members:
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
        proj_map[p.findtext('email')] = t.name
        for m in gh_members:
            print('ADD %s' % m)
            if m in owners:
                # owner can't be maintainer
                t.add_membership(gh_get_user(m))
            else:
                t.add_membership(gh_get_user(m), role='maintainer')

    with open(proj_map_json, 'w') as f:
        json.dump(proj_map, f, indent=0, sort_keys=True)
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
