default: devs.json proj-map.json
all: default all.json
sync: sync-devs sync-projects
clean:
	rm -f devs.json all.json proj-map.json
distclean: clean
	rm -f proxied-maints.json

TOKEN = ~/.github-token

devs.json: ../devs.ldif
	./ldap2devsjson.py $< $@

../devs.ldif:
	+$(MAKE) -C .. devs.ldif

../projects.xml:
	+$(MAKE) -C .. projects.xml

proxied-maints.json: $(TOKEN)
	./update-pr-submitter-db.py $@

all.json: devs.json proxied-maints.json
	./merge-all.py $^ $@

proj-map.json: ../projects.xml $(TOKEN)
	./update-proj-mapping.py $< $@

sync-devs: devs.json $(TOKEN)
	./sync-devs.py $<

sync-projects: devs.json ../projects.xml $(TOKEN)
	./sync-projects.py devs.json ../projects.xml

master.aliases:
	scp dev.gentoo.org:/var/mail/master.aliases .

project-reports: ../projects.xml proj-map.json devs.json master.aliases
	./make-project-report.py $^ proj-reports

.PHONY: default all sync clean distclean
