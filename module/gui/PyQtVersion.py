# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

USE_PYQT5 = None

import os
from sys import exit
from module.gui.CmdLineParser import cmdLineParser

def usePyQt5(pyloadgui_version):

    def importVersion4():
        try:
            from PyQt4.Qt import PYQT_VERSION_STR
            #from PyQt4.Qt import QObject
            return True
        except ImportError:
            return False

    def importVersion5():
        try:
            from PyQt5.Qt import PYQT_VERSION_STR
            return True
        except ImportError:
            return False

    data = cmdLineParser(pyloadgui_version)
    cmdl_ver = data[0]
    configdir_ = data[3]

    if cmdl_ver is not None:
        # use the version number from the command line option
        version = cmdl_ver
    else:
        # read version number from config file
        default_version = 4
        homedir_ = os.path.abspath("")
        if configdir_:
            guiFile = homedir_ + os.sep + "gui.xml"
        else:
            guiFile = os.path.abspath("gui.xml")
        if os.path.isfile(guiFile) and os.access(guiFile, os.R_OK):
            line = None
            with open(guiFile) as t:
                for l in t:
                    l = l.strip()
                    if all(x in l for x in ["<pyqtVersion>", "</pyqtVersion>"]):
                        line = l
                        break
            if line is not None:
                line = line.replace("<pyqtVersion>", "")
                line = line.replace("</pyqtVersion>", "")
                version = line.strip()
                if version:
                    version = int(version)
                    if not (4 <= version <= 5):
                        print "Config file: Bad PyQt version given, trying PyQt%d" % default_version
                        version = default_version
                else:
                    print "Config file: No PyQt version given, trying PyQt%d" % default_version
                    version = default_version
            else:
                print "Config file: PyQt version tag not found, trying PyQt%d" % default_version
                version = default_version
        else:
            print "Config file: File not found or not readable, trying PyQt%d" % default_version
            version = default_version

        # try import
        if version == 4:
            if not importVersion4():
                print "Failed to load PyQt4, trying PyQt5"
                if importVersion5():
                    version = 5
                else:
                    print "Failed to load PyQt5"
                    version = None
        else:
            if not importVersion5():
                print "Failed to load PyQt5, trying PyQt4"
                if importVersion4():
                    version = 4
                else:
                    print "Failed to load PyQt4"
                    version = None

    # return the result or exit the application
    if version == 4:
        return False
    elif version == 5:
        return True
    else:
        print "ERROR: Failed to load PyQt, it is probably not installed"
        exit()


