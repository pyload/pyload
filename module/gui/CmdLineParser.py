# -*- coding: utf-8 -*-

def cmdLineParser(pyloadgui_version):
    from sys import argv
    from getopt import getopt, GetoptError
    import os

    def print_help():
        print ""
        print "pyLoad Client v%s     2008-2016 the pyLoad Team" % pyloadgui_version
        print ""
        if argv[0].endswith(".py"):
            print "Usage: python pyLoadGui.py [options]"
        else:
            print "Usage: pyLoadGui [options]"
        print ""
        print "<Options>"
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -d, --debug=<level>", " " * 4, "Enable debug messages"
        print "                               possible levels: 0 to 9"
        print "  --configdir=<dir>", " " * 6, "Run with <dir> as config directory"
        print "  -c, --connection=<name>", " " * 0, "Use connection <name>"
        print "                               of the Connection Manager"
        print "  -q, --pyqt=<num>", " " * 7, "Force use of PyQt version: 4 or 5"
        print "  -n, --noconsole", " " * 8, "Hide Command Prompt on Windows OS"
        #print "  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>"
        print "  -i, --icontest", " " * 9, "Check for crash when loading icons"
        print "  -h, --help", " " * 13, "Display this help screen"
        print ""

    pyqt       = None
    connection = None
    configdir_ = ""
    noconsole  = False
    icontest   = False
    pidfile    = "pyloadgui.pid"
    debug      = None

    if len(argv) > 1:
        try:
            options, dummy = getopt(argv[1:], 'vq:c:nihd:',
                ["version", "pyqt=", "connection=", "configdir=", "noconsole", "icontest", "help", "debug="])
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
                elif option in ("-c", "--connection"):
                    connection = argument
                elif option in ("--configdir"):
                    configdir_ = argument
                elif option in ("-n", "--noconsole"):
                    if os.name == "nt":
                        noconsole = True
                    else:
                        print "Error: The noconsole option works only on Windows OS"
                        exit()
                elif option in ("-i", "--icontest"):
                    icontest = True
                #elif option in ("-p", "--pidfile"):
                #    pidfile = argument
                #    print "Error: The pidfile option is not implemented"
                #    exit()
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
            print 'Error: Unknown Argument(s) "%s"' % " ".join(argv[1:])
            print_help()
            exit()

    return (pyqt, connection, configdir_, noconsole, icontest, pidfile, debug)


