#!/usr/bin/env python
# vim:fileencoding=utf-8
# Set mirror descriptions and URLs on GitHub
# (c) 2019 Michał Górny, 2-clause BSD licensed

import argparse
import collections
import github
import os.path
import shlex
import sys


RepoTuple = collections.namedtuple('RepoTuple', ('repo', 'desc', 'ghname'))


def process_conf(f):
    url_prefix = 'git@github.com:gentoo/'
    repo = None
    desc = None
    ghname = None
    ret = []

    def commit():
        if ghname is not None:
            assert repo is not None
            assert desc is not None
            ret.append(RepoTuple(repo, desc, ghname))


    for l in f:
        if l.strip().startswith('#'):
            continue
        try:
            sl = shlex.split(l)
        except:
            print(l)
        if not sl:
            continue
        elif sl[0] == 'repo':
            commit()
            repo = sl[1]
            desc = None
            ghname = None
        elif sl[0] == 'desc':
            assert repo is not None
            assert sl[1] == '='
            desc = sl[2]
        elif tuple(sl[:2]) == ('config', 'gentoo.mirror.url'):
            assert repo is not None
            assert sl[2] == '='
            if len(sl) == 3 or not sl[3].startswith(url_prefix):
                continue
            ghname = sl[3][len(url_prefix):]
            if ghname.endswith('.git'):
                ghname = ghname[:-len('.git')]

    commit()
    return ret


def update_mirrors(mirrors, gh):
    o = gh.get_organization('gentoo')

    for r in mirrors:
        print('{} -> {}'.format(r.repo, r.ghname))
        ghr = o.get_repo(r.ghname)
        # gh redirects transferred repos
        if ghr.organization is None:
            print('-> not in gentoo')
            continue
        new_desc = '[MIRROR] {}'.format(r.desc)
        new_url = 'https://gitweb.gentoo.org/' + r.repo + '.git'
        if ghr.description != new_desc or ghr.homepage != new_url:
            ghr.edit(description=new_desc,
                     homepage=new_url)
            print('-> updated')


def update_nonmirrors(mirrors, gh):
    o = gh.get_organization('gentoo')

    all_mirrors = frozenset('gentoo/{}'.format(r.ghname) for r in mirrors)
    for ghr in o.get_repos():
        if ghr.full_name in all_mirrors:
            continue
        print('non-mirror: {}'.format(ghr.full_name))
        # gh redirects transferred repos
        if ghr.organization is None:
            print('-> not in gentoo')
            continue
        if ghr.description is None:
            new_desc = '[ORIGIN] (no description)'
        elif ghr.description.startswith('[ORIGIN]'):
            continue
        else:
            assert not ghr.description.startswith('[MIRROR]')
            new_desc = '[ORIGIN] {}'.format(ghr.description)
        if ghr.archived:
            print('-> archived')
        else:
            ghr.edit(description=new_desc)
            print('-> updated')


def main(argv):
    argp = argparse.ArgumentParser(prog=argv[0])
    argp.add_argument('--api-key-file', type=argparse.FileType('r'),
                      help='File containing the API key',
                      default=os.path.expanduser('~/.github-token'))
    argp.add_argument('file', nargs='+', type=argparse.FileType('r'),
                      help='gitolite configuration files')
    args = argp.parse_args(argv[1:])

    mirrors = []
    for f in args.file:
        mirrors.extend(process_conf(f))

    gh = github.Github(args.api_key_file.read().strip())
    update_mirrors(mirrors, gh)
    update_nonmirrors(mirrors, gh)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
