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

import os
import sys
from sys import exit
from getopt import getopt, GetoptError

def cmdLineParser(pyloadgui_version):

    def print_help():
        print ""
        print "pyLoad Client v%s     2008-2016 the pyLoad Team" % pyloadgui_version
        print ""
        if sys.argv[0].endswith(".py"):
            print "Usage: python pyLoadGui.py [options]"
        else:
            print "Usage: pyLoadGui [options]"
        print ""
        print "<Options>"
        print "  -v, --version            Print version to terminal"
        print "  -d, --debug=<level>      Enable debug messages, possible levels: 0 to 9"
        print "  --configdir=<dir>        Run with <dir> as config directory"
        print "  -c, --connection=<name>  Use connection <name> of the Connection Manager"
        print "  -q, --pyqt=<version>     Force use of PyQt version: 4 or 5"
        print "  -o, --notify=<system>    Force use of Linux desktop notification system:"
        print "                             notify2, pynotify or qt_tray"
        print "  -n, --noconsole          Hide Command Prompt on Windows OSs"
        print "  -p, --pidfile=<file>     Set pidfile to <file>"
        print "  -i, --icontest           Check for crash when loading icons"
        print "  -h, --help               Display this help screen"
        print ""

    pyqt       = None
    desknotify = None
    connection = None
    noconsole  = False
    icontest   = False
    pidfile    = "pyloadgui.pid"
    debug      = None

    if len(sys.argv) > 1:
        try:
            options, dummy = getopt(sys.argv[1:], 'vq:o:c:p:nihd:',
                ["version", "pyqt=", "notify=", "connection=", "pidfile=", "configdir=", "noconsole", "icontest", "help", "debug="])
            for option, argument in options:
                if option in ("-v", "--version"):
                    print pyloadgui_version
                    exit()
                elif option in ("-q", "--pyqt"):
                    try:
                        qtv = int(argument)
                    except ValueError:
                        print "Error: Invalid PyQt version"
                        exit()
                    if not (4 <= qtv <= 5):
                        print "Error: Invalid PyQt version"
                        exit()
                    pyqt = qtv
                elif option in ("-o", "--notify"):
                    if os.name != "nt":
                        desknotify = str(argument)
                        if desknotify not in ["notify2", "pynotify", "qt_tray" ]:
                            print "Error: Invalid desktop notification system"
                            exit()
                    else:
                        print "Error: The notify option works only on Linux/Unix-like OSs"
                        exit()
                elif option in ("-c", "--connection"):
                    connection = argument
                elif option in ("-p", "--pidfile"):
                    pidfile = argument
                elif option in ("-n", "--noconsole"):
                    if os.name == "nt":
                        noconsole = True
                    else:
                        print "Error: The noconsole option works only on Windows OSs"
                        exit()
                elif option in ("-i", "--icontest"):
                    icontest = True
                elif option in ("-h", "--help"):
                    print_help()
                    exit()
                elif option in ("-d", "--debug"):
                    try:
                        lvl = int(argument)
                    except ValueError:
                        print "Error: Invalid debug level"
                        exit()
                    if not (0 <= lvl <= 9):
                        print "Error: Invalid debug level"
                        exit()
                    debug = lvl

        except GetoptError:
            print 'Error: Unknown Argument(s) "%s"' % " ".join(sys.argv[1:])
            print_help()
            exit()

    return (pyqt, desknotify, connection, noconsole, icontest, pidfile, debug)


