#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import walk, remove
from os.path import join
from subprocess import call


options = ["--from-code=utf-8", "--copyright-holder=pyLoad Team", "--package-name=pyLoad", "--package-version=0.4.8",
           "--msgid-bugs-address='bugs@pyload.org'"]


def po2pot(name):
    f = open("%s.po" % name, "rb")
    content = f.read()
    f.close()
    remove("core.po")
    content = content.replace("charset=CHARSET", "charset=UTF-8")

    f = open("locale/%s.pot" % name, "wb")
    f.write(content)
    f.close()

###### Core

EXCLUDE = ["BeautifulSoup.py", "module/gui", "module/cli", "web/locale", "web/ajax", "web/cnl", "web/pyload", "setup.py"]
print "Generate core.pot"

f = open("includes.txt", "wb")
f.write("./pyLoadCore.py\n")

for path, dir, filenames in walk("./module"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if file.endswith(".py") and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=core"] + options)
po2pot("core")

########## GUI

print "Generate gui.pot"

EXCLUDE = []

f = open("includes.txt", "wb")
f.write("./pyLoadGui.py\n")

for path, dir, filenames in walk("./module/gui"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if file.endswith(".py") and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=gui"] + options)
po2pot("gui")


###### CLI

print "Generate cli.pot"

f = open("includes.txt", "wb")
f.write("./pyLoadCli.py\n")

for path, dir, filenames in walk("./module/cli"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if file.endswith(".py") and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=cli"] + options)
po2pot("cli")

###### Setup

print "Generate setup.pot"

f = open("includes.txt", "wb")
f.write("./module/setup.py\n")
f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=setup"] + options)
po2pot("setup")

### Web

EXCLUDE = ["ServerThread.py", "web/media/"]
print "Generate django.pot (old name keeped)"

f = open("includes.txt", "wb")
for path, dir, filenames in walk("./module/web"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if (file.endswith(".py") or file.endswith(".html") or file.endswith(".js")) and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=django", "--language=Python"] + options)
po2pot("django")

print
print "All finished."
