#!/usr/bin/env python
# vim:fileencoding=utf-8
# Write project mapping from e-mails to Codeberg
# 2-clause BSD licensed

import json
import os.path
import sys

import lxml.etree
from codebergapi import CodebergAPI


def main(projects_xml="projects.xml", proj_map_json="proj-map.json"):
    with open(os.path.expanduser("~/.codeberg-token")) as f:
        api_token = f.read().strip()

    projs_x = lxml.etree.parse(projects_xml)
    projs = {}
    for p in projs_x.getroot():
        projs[p.findtext("email").split("@")[0].lower()] = p
        projs[p.findtext("name").split("@")[0].lower()] = p
        projs[p.findtext("url").split(":")[2].lower()] = p

    proj_map = {}
    rem_projs = set(p for p in projs_x.getroot())

    with CodebergAPI("gentoo", "gentoo", api_token) as cb:
        for t in cb.teams("gentoo"):
            tname = t["name"]
            p = projs.get(tname.lower())
            if p is None:
                print(f"{tname} <-> ?")
            else:
                print(f"{tname} <-> {p}")
                proj_map[p.findtext("email").lower()] = "gentoo/" + tname
                rem_projs.remove(p)

    for p in rem_projs:
        print(f"MISSING PROJECT: {p.findtext('email')}")

    with open(proj_map_json, "w") as f:
        json.dump(proj_map, f, indent=0, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
