all: devs.json projects.xml
clean:
	rm -f devs.txt devs.json projects.xml

devs.json: devs.txt
	./ldap2devsjson.py $< $@

devs.txt:
	ssh dev.gentoo.org '/usr/local/bin/perl_ldap -S gentooGitHubUser' > $@
	
projects.xml:
	wget -O $@ https://api.gentoo.org/metastructure/projects.xml

.PHONY: all clean
