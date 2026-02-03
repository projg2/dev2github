#!/usr/bin/env python
# vim:fileencoding=utf-8
# Sync projects to Codeberg
# 2-clause BSD licensed

import json
import os.path
import sys

import lxml.etree
from codebergapi import CodebergAPI


ORG = "gentoo"


def add_members(members, p, xmltree):
    members += [m.findtext("email").lower() for m in p.findall("member")]

    for subp in p.findall("subproject"):
        if subp.get("inherit-members") == "1":
            subp_email = subp.get("ref")
            for op in xmltree:
                if op.findtext("email") == subp_email:
                    add_members(members, op, xmltree)


def main(devs_json="devs.json", projects_xml="projects.xml"):
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)

    with open(os.path.expanduser("~/.codeberg-token")) as f:
        api_token = f.read().strip()

    projs_x = lxml.etree.parse(projects_xml)
    projs = {}
    for p in projs_x.getroot():
        projs[p.findtext("email").split("@")[0].lower()] = p
        projs[p.findtext("name").split("@")[0].lower()] = p
        projs[p.findtext("url").split(":")[2].lower()] = p

    cb_devs = set(devs.values())
    rem_projs = set(p for p in projs_x.getroot())

    with CodebergAPI("gentoo", "gentoo", api_token) as cb:
        teams_to_delete = []
        for t in cb.teams(ORG):
            team_id = t["id"]
            team_name = t["name"]
            if team_name == "Owners":  # skip special Owners team
                continue
            p = projs.get(team_name.lower())
            if p is None:
                print(f"{team_name} <-> ?")
                continue
            print(f"{team_name} <-> {p}")
            rem_projs.remove(p)
            members = []
            add_members(members, p, projs_x.getroot())

            # all project members mapped to codeberg logins
            cb_members = set(devs[x] for x in members if devs.get(x))
            # all team members as listed in Codeberg
            team_members = set(u["login"] for u in cb.team_members(team_id))

            # Codeberg members that are not project members
            extra_cb_members = team_members - cb_members

            # remove extraneous gh team members that do have dev acct
            # (i.e. most likely left the team)
            for m in extra_cb_members:
                if m in cb_devs:
                    print(f"REMOVE {m}")
                    cb.team_remove_member(team_id, m)
                    team_members.discard(m)

            # Project members not listed in team
            extra_devs = cb_members - team_members
            for m in extra_devs:
                print(f"ADD {m}")
                cb.team_add_member(team_id, m)
                team_members.add(m)

            # empty now? remove it
            if not team_members:
                if next(cb.team_repos(team_id), None):
                    print("EMPTY TEAM WITH REPOS")
                else:
                    print("DELETE TEAM")
                    teams_to_delete.append(team_id)

        for team_id in teams_to_delete:
            cb.org_delete_team(team_id)

    for p in rem_projs:
        names = [
            p.findtext("email").split("@")[0],
            p.findtext("name").lower(),
            p.findtext("name"),
            p.findtext("url").split(":")[2].lower(),
            p.findtext("url").split(":")[2],
        ]
        seen = {}
        names = [seen.setdefault(x, x) for x in names if x not in seen]
        desc = p.findtext("description")
        if len(desc) >= 255:
            desc = desc[:254] + "…"
        members = []
        add_members(members, p, projs_x.getroot())

        if not members:
            if not p.findall("subproject"):
                print(f"WARN: {names[0]} project has no developers!")
            else:
                print(f"NOTE: {names[0]} project purely organizational (no members)")
            continue
        cb_members = [devs[m] for m in members if devs.get(m)]
        if not cb_members:
            print(f"NOTE: {names[0]} project has no Codeberg users")
            continue

        print("== NEW PROJECT ==")
        print("Name:")
        for i, n in enumerate(names):
            print(f"{i + 1}) {n}")
            print(f"Desc: {desc}")
            print(f"Members: {members}")
            print(f"Codeberg Members: {cb_members}")
        while True:
            resp = input("Proceed? [Y/n/1..%d]" % len(names))
            if resp.lower() in ["", "y", "n"] + [
                str(x) for x in range(1, len(names) + 1)
            ]:
                break
            print("Unrecognized reply: %s" % resp)
        if resp.lower() == "n":
            continue
        if resp.lower() in ("", "y"):
            resp = "1"
        name = names[int(resp) - 1]

        print(f"CREATE TEAM {name}")
        t = cb.create_team(ORG, name, desc)
        team_id = t["id"]
        for m in cb_members:
            print(f"ADD {m}")
            cb.team_add_member(team_id, m)

    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
