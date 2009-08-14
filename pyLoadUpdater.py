import urllib
import urllib2
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 RaNaN
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###

## read version from core
import re
import zipfile
import os

class Unzip:
    def __init__(self):
        pass
        
    def extract(self, file, dir):
        if not dir.endswith(':') and not os.path.exists(dir):
            os.mkdir(dir)

        zf = zipfile.ZipFile(file)

        # create directory structure to house files
        self._createstructure(file, dir)

        # extract files to directory structure
        for i, name in enumerate(zf.namelist()):

            if not name.endswith('/') and not name.endswith("config"):
                print "extracting", name.replace("pyload/","")
                outfile = open(os.path.join(dir, name.replace("pyload/","")), 'wb')
                outfile.write(zf.read(name))
                outfile.flush()
                outfile.close()

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def _makedirs(self, directories, basedir):
        """ Create any directories that don't currently exist """
        for dir in directories:
            curdir = os.path.join(basedir, dir)
            if not os.path.exists(curdir):
                os.mkdir(curdir)

    def _listdirs(self, file):
        """ Grabs all the directories in the zip structure
        This is necessary to create the structure before trying
        to extract the file to it. """
        zf = zipfile.ZipFile(file)

        dirs = []

        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name.replace("pyload/",""))

        dirs.sort()
        return dirs

def main():
    print "Updating pyLoad"

    try:
        f = open("pyLoadCore.py", "rb")
        version = re.search(r"CURRENT_VERSION = '([0-9.]+)'",f.read()).group(1)
        f.close()
    except:
        version = "0.0.0"

    print "Your version:", version

    req = urllib2.urlopen("http://update.pyload.org/index.php?do="+version)
    result = req.readline()

    if result == "False":
        print "pyLoad is up-to-date, nothing to do."
        return False

    req = urllib2.urlopen("http://update.pyload.org/index.php")
    result = req.readline()
    print "Newest Version:", result
    print "Download new Version"

    urllib.urlretrieve("http://update.pyload.org/index.php?do=download", "lastest_version.zip")

    u = Unzip()
    u.extract("lastest_version.zip",".")

if __name__ == "__main__":
    main()
