default: devs.ldif projects.xml
	+$(MAKE) -C codeberg default
	+$(MAKE) -C github default

devs.ldif:
	ssh dev.gentoo.org "ldapsearch -x '(gentooStatus=active)' -Z uid mail gentooCodebergUser gentooGitHubUser -LLL" > $@

projects.xml:
	wget -O $@ https://api.gentoo.org/metastructure/projects.xml

clean:
	+$(MAKE) -C codeberg clean
	+$(MAKE) -C github clean
	rm devs.ldif projects.xml

sync: default
	+$(MAKE) -C codeberg sync
	+$(MAKE) -C github sync

.PHONY: clean default sync
