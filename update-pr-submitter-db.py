#!/usr/bin/env python
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
            c1 = pr.get_commits()[0]
            if c1.committer != pr.user:
                print("\nPR submitter (%s) != committer (%s)" %
                        (pr.user, c1.committer))
                continue
            print('\n%s -> %s' % (c1.commit.committer.email, c1.committer.login))
            maints[c1.commit.committer.email] = c1.committer.login

            with open(proxied_maints_json, 'w') as pm_f:
                json.dump(maints, pm_f)

    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
