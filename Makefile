all: devs.json projects.xml
clean:
	rm -f devs.ldif devs.json projects.xml

devs.json: devs.ldif
	./ldap2devsjson.py $< $@

devs.ldif:
	ssh dev.gentoo.org "ldapsearch '(gentooStatus=active)' -Z uid mail gentooGitHubUser -LLL" > $@
	
projects.xml:
	wget -O $@ https://api.gentoo.org/metastructure/projects.xml

.PHONY: all clean
