#!/usr/bin/env python
# vim:fileencoding=utf-8
# Create or update JSON mapping of email->codeberg for pull request
# submitters
# 2-clause BSD licensed

import json
import os
import os.path
import sys

from codebergapi import CodebergAPI


def main(proxied_maints_json="proxied-maints.json"):
    maints = {}
    try:
        with open(proxied_maints_json) as pm_f:
            maints = json.load(pm_f)
    except (OSError, IOError):
        pass

    with open(os.path.expanduser("~/.codeberg-token")) as f:
        api_token = f.read().strip()

    with CodebergAPI("gentoo", "gentoo", api_token) as cb:
        for pr in cb.pulls(state="all"):
            print(f"PR #{pr['number']:04d}", end="")

            pr_user = pr["user"]["login"]
            if pr_user not in maints.values():
                commits = cb.commits(pr["number"])
                if len(commits) == 0:
                    continue

                need_confirm = False
                c1 = commits[0]
                attributed = c1["committer"]
                attributed_c = c1["commit"]["committer"]

                if attributed is None:
                    attributed = c1["author"]
                    attributed_c = c1["commit"]["author"]

                if attributed is None:
                    # Codeberg wasn't able to match the committer nor
                    # author fields to a user name. Prefer suggesting
                    # the committer email matched to the PR submitter
                    # login over the author email
                    print(pr["html_url"])
                    print(pr["patch_url"])
                    print(f"PR #{pr['number']}: commit not matched to a user")
                    attributed = pr["user"]
                    attributed_c = c1["commit"]["committer"]
                    print(
                        f"{attributed_c['email']} ({attributed_c['name']}) -> {attributed['login']} ({attributed['full_name']})"
                    )
                    need_confirm = True

                if attributed["login"] != pr_user and c1["author"]["login"] == pr_user:
                    attributed = c1["author"]
                    attributed_c = c1["commit"]["author"]

                if attributed["login"] == pr_user:
                    print(f"\n{attributed_c['email']} -> {attributed['login']}")
                else:
                    # In this case: committer, author, and PR
                    # submitter are all matched to three different
                    # Codeberg users.
                    print(pr["html_url"])
                    print(pr["patch_url"])
                    print(
                        "PR submitter matches none of committer or author users. Skipping."
                    )
                    continue

                if need_confirm:
                    escape = False
                    while True:
                        resp = input("-> Proceed? [Y/n]")
                        if resp.lower() == "y" or not resp:
                            break
                        elif resp.lower() == "n":
                            escape = True
                            break
                    if escape:
                        continue
                maints[attributed_c["email"]] = attributed["login"]

    with open(proxied_maints_json, "w") as pm_f:
        json.dump(maints, pm_f, indent=2)

    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
