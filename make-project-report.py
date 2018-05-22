#!/usr/bin/env python
# vim:fileencoding=utf-8
# Make a report of project members & data
# (c) 2017 Michał Górny, 2-clause BSD licensed

import email.charset
import email.message
import email.utils
import json
import os
import pwd
import sys
import textwrap

import lxml.etree


class Member(object):
    __slots__ = ('xml', 'gh', 'on_alias')

    def __init__(self, xml, devs, aliases):
        self.xml = xml
        self.gh = devs.get(self.email.lower())
        if self.gh == "":
            self.gh = None
        self.on_alias = self.email.lower() in aliases

    @property
    def email(self):
        return self.xml.findtext('email')

    @property
    def name(self):
        return self.xml.findtext('name')

    @property
    def role(self):
        return self.xml.findtext('role')

    @property
    def is_lead(self):
        return bool(int(self.xml.get('is-lead', '0')))

    @property
    def on_github(self):
        return self.gh is not None


class Subproject(object):
    __slots__ = ('xml')

    def __init__(self, xml):
        self.xml = xml

    @property
    def email(self):
        return self.xml.get('ref')

    @property
    def inherit_members(self):
        return bool(int(self.xml.get('inherit-members', '0')))


class Project(object):
    __slots__ = ('xml', 'gh', 'devs', 'aliases')

    def __init__(self, xml, proj_map, devs, aliases):
        self.xml = xml
        self.gh = proj_map.get(self.email.lower())
        self.devs = devs
        self.aliases = aliases

    @property
    def email(self):
        return self.xml.findtext('email')

    @property
    def name(self):
        return self.xml.findtext('name')

    @property
    def url(self):
        return self.xml.findtext('url')

    @property
    def github(self):
        if self.gh is not None:
            return ('https://github.com/orgs/%s/teams/%s/members'
                    % tuple(self.gh.split('/')))
        return None

    @property
    def description(self):
        return self.xml.findtext('description')

    @property
    def members(self):
        for m in self.xml.findall('member'):
            yield Member(m, self.devs,
                    self.aliases.get(self.email.split('@')[0].lower(), ()))

    @property
    def subprojects(self):
        for sp in self.xml.findall('subproject'):
            yield Subproject(sp)


def format_subject_for_project(p):
    return 'Status report for %s project' % p.email


def format_body_for_project(p):
    body = '''Hi,

As an effort to ensure our projects are healthy, I'm sending this mail
to every project in Gentoo. It includes a summary of how the project
is registered, and is a friendly ping in case you need any help. Here's
the data, followed by detailed instructions. Please look through it
and reply accordingly.


Project name: {name}
Contact address: {email}
Wiki URL: {url} [1]
GitHub URL: {github}
Description: {description}

Member list:

'''.format(name=p.name, email=p.email, url=p.url, github=(p.github or '(none)'),
           description='\n'.join(textwrap.wrap(p.description)))

    for m in p.members:
        body += '''  {email:>24}  {is_lead} {on_alias} {on_github}
'''.format(email=m.email, name=m.name, role=m.role,
           is_lead='L' if m.is_lead else ' ',
           on_alias='A' if m.on_alias else ' ',
           on_github='G' if m.on_github else ' ')

    body += '''
Legend:
  L - project lead
  A - on project alias
  G - on github team
'''

    subprojects = list(p.subprojects)
    if subprojects:
        body += '''
Subprojects:

'''

        for sp in subprojects:
            body += '''  {email:>24}{inherit_members}
'''.format(email=sp.email,
           inherit_members='  [members inherited]' if sp.inherit_members else '')
    

    body += '''

Instructions
------------

1. The project data and member list is obtained from the Gentoo wiki.
If anything in the description is wrong, there are members missing etc.
please visit [1] and use the edit form to update the project info.

2. The alias state was obtained from woodpecker. Please note that my
poor man's check accounted only for direct membership, so if you are
included in the alias indirectly, it won't figure that out. If you find
anything wrong with that, please edit the appropriate alias files
on dev.gentoo.org:

  vim /var/mail/alias/*/{emailshort}

3. The GitHub state is automatically synced based on GitHub usernames
in LDAP. If there is something wrong with that, please make sure you've
got your gentooGitHubUser field in LDAP set correctly and ping me to
run the sync script.

4. If you believe that your project needs more people working on it,
please either send a 'call for members' yourself or let me know that
I should do it.

5. If you believe that your project should be disbanded, please make
sure to remove all its occurrences from metadata.xml files first,
and afterwards use 'edit source' on the wiki [1] to wipe the content
off the project page (do not use 'delete' as it will remove history).
Alternatively, just let me know.

6. If everything is fine, please just reply to me with a simple 'ACK'.
Make sure to keep your project CC-ed so that I do not get multiple
replies ;-).

7. If I do not receive any reply within a reasonable time, I will
assume that the project needs volunteers. I will assemble a list
of projects that did not reply and will bring the topic of helping them
to the mailing list.

If you have any questions, feel free to ask.
'''.format(emailshort=p.email.split('@')[0])

    return body


def main(projects_xml='projects.xml', proj_map_json='proj-map.json',
        devs_json='devs.json', master_aliases='master.aliases',
        proj_reports='proj-reports'):
    projs_x = lxml.etree.parse(projects_xml)
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)
    with open(proj_map_json) as proj_map_f:
        proj_map = json.load(proj_map_f)
    aliases = {}
    with open(master_aliases) as master_aliases_f:
        for l in master_aliases_f:
            k, v = l.split(':')
            gentooize = lambda u: ('%s@gentoo.org' % u if '@' not in u
                                   and not u.startswith('/')
                                   else u)
            aliases[k.strip().lower()] = [
                    gentooize(u.strip().lower()) for u in v.split(',')]

    # the default charset is insane
    charset = email.charset.Charset('utf-8')
    charset.header_encoding = email.charset.QP
    charset.body_encoding = email.charset.QP

    # find out who I am
    pwent = pwd.getpwuid(os.getuid())
    email_from = pwent[0] + '@gentoo.org'
    fullname = pwent[4]
    signature = '''
--
Yours sincerely,
{}'''.format(fullname)

    os.makedirs(proj_reports, exist_ok=True)
    for px in projs_x.getroot():
        p = Project(px, proj_map, devs, aliases)

        msg = email.message.Message()
        msg.set_charset(charset)
        msg.set_payload(charset.body_encode(format_body_for_project(p)
                                            + signature))
        msg['From'] = email.utils.formataddr((fullname, email_from))
        msg['To'] = email.utils.formataddr((p.name, p.email))
        msg['BCC'] = email.utils.formataddr((fullname, email_from))
        msg['Subject'] = format_subject_for_project(p)
        msg['Date'] = email.utils.formatdate()
        msg['Message-Id'] = email.utils.make_msgid()

        with open(os.path.join(proj_reports, p.email.split('@')[0]), 'wb') as f:
            f.write(bytes(msg))


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
