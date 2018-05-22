#!/usr/bin/env python
# vim:fileencoding=utf-8
# Create or update JSON mapping of email->gh for pull request submitters
# (c) 2016 Michał Górny, 2-clause BSD licensed

import json
import os
import os.path
import sys

import github


def main(proxied_maints_json='proxied-maints.json'):
    maints = {}
    try:
        with open(proxied_maints_json) as pm_f:
            maints = json.load(pm_f)
    except (OSError, IOError):
        pass

    with open(os.path.expanduser('~/.github-token')) as f:
        gh = github.Github(f.read().strip())

    r = gh.get_repo('gentoo/gentoo')
    for pr in r.get_pulls(state='all'):
        print("\rPR #%04d" % pr.number, end='')
        if pr.user.login not in maints.values():
            if pr.commits == 0:
                continue
            need_confirm = False
            c1 = pr.get_commits()[0]
            attributed = c1.committer
            attributed_c = c1.commit.committer
            if attributed != pr.user and c1.author == pr.user:
                attributed = c1.author
                attributed_c = c1.commit.author

            if attributed != pr.user:
                print('')
                print(pr.html_url)
                print(pr.patch_url)
                print("PR submitter (%s) != committer (%s)" %
                        (pr.user, c1.committer))
                if c1.committer is None:
                    attributed = pr.user
                    print('%s (%s) -> [PR] %s (%s)' % (attributed_c.email,
                        c1.commit.committer.name, attributed.login, attributed.name))
                else:
                    attributed = c1.committer
                    print('%s (%s) -> %s (%s)' % (attributed_c.email,
                        c1.commit.committer.name, attributed.login, attributed.name))
                need_confirm = True
            else:
                print('\n%s -> %s' % (attributed_c.email, attributed.login))

            if need_confirm:
                escape = False
                while True:
                    resp = input('-> Proceed? [Y/n]')
                    if resp.lower() == 'y' or not resp:
                        break
                    elif resp.lower() == 'n':
                        escape = True
                        break
                if escape:
                    continue

            maints[attributed_c.email] = attributed.login

            with open(proxied_maints_json, 'w') as pm_f:
                json.dump(maints, pm_f)

    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
