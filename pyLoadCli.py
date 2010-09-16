#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2010 RaNaN
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
from getopt import GetoptError
from getopt import getopt
import gettext
from itertools import islice
import os
import os.path
from os.path import join
import sys
from sys import exit
import threading
from time import sleep
import xmlrpclib
from traceback import print_exc

from codecs import getwriter
sys.stdout = getwriter("utf8")(sys.stdout, errors = "replace")

from module import InitHomeDir
from module.ConfigParser import ConfigParser

if sys.stdout.encoding.lower().startswith("utf"):
    conv = unicode
else:
    conv = str

class pyLoadCli:
    def __init__(self, server_url, add=False):
        self.core = xmlrpclib.ServerProxy(server_url, allow_none=True)
        self.getch = _Getch()
        self.input = ""
        self.pos = [0, 0, 0]
        self.inputline = 0
        self.menuline = 0

        self.new_package = {}

        try:
            self.core.get_server_version()
        except:
            print _("pyLoadCore not running")
            exit()

        self.links_added = 0

        os.system("clear")
        self.println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
        self.println(2, "")


        self.file_list = {}

        self.thread = RefreshThread(self)
        self.thread.start()

        self.start()

    def start(self):
        while True:
            #inp = raw_input()
            inp = self.getch.impl()
            if ord(inp) == 3:
                os.system("clear")
                sys.exit() # ctrl + c
            elif ord(inp) == 13:
                try:
                    self.handle_input()
                except Exception, e:
                    self.println(2, red(conv(e)))
                self.input = ""   #enter
                self.print_input()
            elif ord(inp) == 127:
                self.input = self.input[:-1] #backspace
                self.print_input()
            elif ord(inp) == 27: #ugly symbol
                pass
            else:
                self.input += inp
                self.print_input()

    def format_time(self, seconds):
        seconds = int(seconds)

        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)

    def format_size(self, size):
        return conv(size / 1024 ** 2) + " MiB"

    def println(self, line, content):
        print "\033[" + conv(line) + ";0H\033[2K" + content + "\033[" + conv((self.inputline if self.inputline > 0 else self.inputline + 1) - 1) + ";0H"

    def print_input(self):
        self.println(self.inputline, white(" Input: ") + self.input)
        self.println(self.inputline + 1, "")
        self.println(self.inputline + 2, "")
        self.println(self.inputline + 3, "")
        self.println(self.inputline + 4, "")

    def refresh(self):
        """Handle incoming data"""
        data = self.core.status_downloads()
            #print updated information
        print "\033[J" #clear screen
        self.println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
        self.println(2, "")
        self.println(3, white(_("%s Downloads:") % (len(data))))
        line = 4
        speed = 0
        for download in data:
            if download["status"] == 12:  # downloading
                percent = download["percent"]
                z = percent / 4
                speed += download['speed']
                self.println(line, cyan(download["name"]))
                line += 1
                self.println(line, blue("[") + yellow(z * "#" + (25-z) * " ") + blue("] ") + green(conv(percent) + "%") + _(" Speed: ") + green(conv(int(download['speed'])) + " kb/s") + _(" Size: ") + green(download['format_size']) + _(" Finished in: ") + green(download['format_eta'])  + _(" ID: ") + green(conv(download['id'])))
                line += 1
            if download["status"] == 5:
                self.println(line, cyan(download["name"]))
                line += 1
                self.println(line, _("waiting: ") + green(download["format_wait"]) )
                line += 1
        self.println(line, "")
        line += 1
        status = self.core.status_server()
        if status['pause']:
            self.println(line, _("Status: ") + red("paused") + _(" total Speed: ") + red(conv(int(speed)) + " kb/s") + _(" Files in queue: ") + red(conv(status["queue"])))
        else:
            self.println(line, _("Status: ") + red("running") + _(" total Speed: ") + red(conv(int(speed)) + " kb/s") + _(" Files in queue: ") + red(conv(status["queue"])))
        line += 1
        self.println(line, "")
        line += 1
        self.menuline = line

        self.build_menu()
        #
        self.file_list = data

    def build_menu(self):
        line = self.menuline
        self.println(line, white(_("Menu:")))
        line += 1
        if self.pos[0] == 0:# main menu
            self.println(line, "")
            line += 1
            self.println(line, mag("1.") + _(" Add Links"))
            line += 1
            self.println(line, mag("2.") + _(" Manage Links"))
            line += 1
            self.println(line, mag("3.") + _(" (Un)Pause Server"))
            line += 1
            self.println(line, mag("4.") + _(" Kill Server"))
            line += 1
            self.println(line, mag("5.") + _(" Quit"))
            line += 1
            self.println(line, "")
            line += 1
            self.println(line, "")
        elif self.pos[0] == 1:#add links

            if self.pos[1] == 0:
                self.println(line, "")
                line += 1
                self.println(line, _("Name your package."))
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, mag("0.") + _(" back to main menu"))
                line += 1
                self.println(line, "")

            else:
                self.println(line, _("Package: %s") % self.new_package['name'])
                line += 1
                self.println(line, _("Parse the links you want to add."))
                line += 1
                self.println(line, _("Type %s when done.") % mag("END"))
                line += 1
                self.println(line, _("Links added: ") + mag(conv(self.links_added)))
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, mag("0.") + _(" back to main menu"))
                line += 1
                self.println(line, "")
        elif self.pos[0] == 2:#remove links
            if self.pos[1] == 0:
                pack = self.core.get_queue()
                self.println(line, _("Type d(number of package) to delete a package, r to restart, or w/o d,r to look into it."))
                line += 1
                i = 0
                for id, value in islice(pack.iteritems(), self.pos[2], self.pos[2] + 5):
                    try:
                        self.println(line, mag(conv(id)) + ": " + value['name'])
                        line += 1
                        i += 1
                    except Exception, e:
                        pass
                for x in range(5-i):
                    self.println(line, "")
                    line += 1

            else:
                links = self.core.get_package_data(self.pos[1])
                self.println(line, _("Type d(number) of the link you want to delete or r(number) to restart."))
                line += 1
                i = 0
                for id, value in islice(links["links"].iteritems(), self.pos[2], self.pos[2] + 5):
                    try:

                        self.println(line, mag(conv(id)) + ": %s | %s | %s" % (value['name'], value['statusmsg'], value['plugin']))
                        line += 1
                        i += 1

                    except Exception, e:
                        pass
                for x in range(5-i):
                    self.println(line, "")
                    line += 1

            self.println(line, mag("p") + _(" - previous") + " | " + mag("n") + _(" - next"))
            line += 1
            self.println(line, mag("0.") + _(" back to main menu"))

        self.inputline = line + 1
        self.print_input()

    def handle_input(self):
        inp = self.input.strip()
        if inp == "0":
            self.pos = [0, 0, 0]
            self.build_menu()
            return True

        if self.pos[0] == 0:
            if inp == "1":
                self.links_added = 0
                self.pos[0] = 1
            elif inp == "2":
                self.pos[0] = 2
                self.pos[1] = 0
            elif inp == "3":
                self.core.toggle_pause()
            elif inp == "4":
                self.core.kill()
                sys.exit()
            elif inp == "5":
                os.system('clear')
                sys.exit()

        elif self.pos[0] == 1: #add links
            if self.pos[1] == 0:
                self.new_package['name'] = inp
                self.new_package['links'] = []
                self.pos[1] = 1
            else:
                if inp == "END":
                    self.core.add_package(self.new_package['name'], self.new_package['links'], 1) # add package
                    self.pos = [0, 0, 0]
                    self.links_added = 0
                else: #TODO validation
                    self.new_package['links'].append(inp)
                    self.links_added += 1

        elif self.pos[0] == 2: #remove links
            if self.pos[1] == 0:
                if inp.startswith("d"):
                    if inp.find("-") > -1:
                        self.core.del_packages(range(*map(int, inp[1:].split("-"))))
                    else:
                        self.core.del_packages([int(inp[1:])])
                if inp.startswith("r"):
                    self.core.restart_package(int(inp[1:]))
                elif inp != "p" and inp != "n":
                    self.pos[1] = int(inp)
                    self.pos[2] = 0
            elif inp.startswith('r'):
                if inp.find("-") > -1:
                    map(self.core.restart_file, range(*map(int, inp[1:].split("-"))))
                else:
                    self.core.restart_file(int(inp[1:]))
            elif inp.startswith('d') and inp != "p" and inp != "n":
                if inp.find("-") > -1:
                    self.core.del_links(range(*map(int, inp[1:].split("-"))))
                else:
                    self.core.del_links([int(inp[1:])])
            if inp == "p":
                self.pos[2] -= 5
            elif inp == "n":
                self.pos[2] += 5

        self.build_menu()

class RefreshThread(threading.Thread):
    def __init__(self, cli):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.cli = cli

    def run(self):
        while True:
            sleep(1)
            try:
                self.cli.refresh()
            except Exception, e:
                self.cli.println(2, red(conv(e)))
                self.cli.pos[1] = 0
                self.cli.pos[2] = 0
                print_exc()




class _Getch:
    """
    Gets a single character from standard input.  Does not echo to
    the screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            try:
                self.impl = _GetchMacCarbon()
            except(AttributeError, ImportError):
                self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty
        import sys

    def __call__(self):
        import sys
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

class _GetchMacCarbon:
    """
    A function which returns the current ASCII key that is down;
    if no ASCII key is down, the null string is returned.  The
    page http://www.mactech.com/macintosh-c/chap02-1.html was
    very helpful in figuring out how to do this.
    """
    def __init__(self):
        import Carbon
        Carbon.Evt #see if it has this (in Unix, it doesn't)

    def __call__(self):
        import Carbon
        if Carbon.Evt.EventAvail(0x0008)[0] == 0: # 0x0008 is the keyDownMask
            return ''
        else:
            #
            # The event contains the following info:
            # (what,msg,when,where,mod)=Carbon.Evt.GetNextEvent(0x0008)[1]
            #
            # The message (msg) contains the ASCII char which is
            # extracted with the 0x000000FF charCodeMask; this
            # number is converted to an ASCII character with chr() and
            # returned
            #
            (what, msg, when, where, mod) = Carbon.Evt.GetNextEvent(0x0008)[1]
            return chr(msg)

def blue(string):
    return "\033[1;34m" + string + "\033[0m"

def green(string):
    return "\033[1;32m" + string + "\033[0m"

def yellow(string):
    return "\033[1;33m" + string + "\033[0m"

def red(string):
    return "\033[1;31m" + string + "\033[0m"

def cyan(string):
    return "\033[1;36m" + string + "\033[0m"

def mag(string):
    return "\033[1;35m" + string + "\033[0m"

def white(string):
    return "\033[1;37m" + string + "\033[0m"

def print_help():
    print ""
    print "pyLoadCli Copyright (c) 2008-2010 the pyLoad Team"
    print ""
    print "Usage: [python] pyLoadCli.py [options] [server url]"
    print ""
    print "<server url>"
    print "The server url has this format: http://username:passwort@address:port"
    print ""
    print "<Options>"
    print "  -l, --local", " " * 6, "Use the local settings in config file"
    print "  -u, --username=<username>"
    print " " * 20, "Specify username"
    print ""
    print "  -a, --address=<address>"
    print " " * 20, "Specify address (default=127.0.0.1)"
    print ""
    print "  --linklist=<path>"
    print " " * 20, "Add container to pyLoad"
    print ""
    print "  -p, --port", " " * 7, "Specify port (default=7272)"
    print "  -s, --ssl", " " * 8, "Enable ssl (default=off)"
    print "  -h, --help", " " * 7, "Display this help screen"
    print "  --pw=<password>", " " * 2, "Password (default=ask for it)"
    print "  -c, --command=", " "* 3, "Sends a command to pyLoadCore (use help for list)"
    print ""



if __name__ == "__main__":
    config = ConfigParser()

    translation = gettext.translation("pyLoadCli", join(pypath, "locale"), languages=["en", config['general']['language']])
    translation.install(unicode=True)

    server_url = ""
    username = ""
    password = ""
    addr = ""
    port = ""
    ssl = None
    #############
    command = None
    #############

    add = ""

    if len(sys.argv) > 1:


        addr = "127.0.0.1"
        port = "7272"
        ssl = ""

        shortOptions = 'lu:a:p:s:hc:' #hier das c angefügt
        longOptions = ['local', "username=", "address=", "port=", "ssl=", "help", "linklist=", "pw=", "command="]

        try:
            opts, extraparams = getopt(sys.argv[1:], shortOptions, longOptions)
            for option, params in opts:
                if option in ("-l", "--local"):

                    if config['ssl']['activated']:
                        ssl = "s"

                    username = config.username
                    password = config.password
                    addr = config['remote']['listenaddr']
                    port = config['remote']['port']
                elif option in ("-u", "--username"):
                    username = params
                elif option in ("-a", "--address"):
                    addr = params
                elif option in ("-p", "--port"):
                    port = params
                elif option in ("-s", "--ssl"):
                    if params.lower() == "true":
                        ssl = "s"
                elif option in ("-h", "--help"):
                    print_help()
                    exit()
                elif option in ("--linklist"):
                    add = params
                elif option in ("--pw"):
                    password = params
                elif option in ("-c"):
                    command = params

        except GetoptError:
            print 'Unknown Argument(s) "%s"' % " ".join(sys.argv[1:])
            print_help()
            exit()

        if len(extraparams) == 1:
            server_url = sys.argv[1]

    if not server_url:
        if not username: username = raw_input(_("Username: "))
        if not addr: addr = raw_input(_("address: "))
        if ssl is None:
            ssl = raw_input(_("Use SSL? ([y]/n): "))
            if ssl == "y" or ssl == "":
                ssl = "s"
            else:
                ssl = ""
        if not port: port = raw_input(_("Port: "))
        if not password:
            from getpass import getpass
            password = getpass(_("Password: "))

        server_url = "http%s://%s:%s@%s:%s/" % (ssl, username, password, addr, port)

    if command:
        core = xmlrpclib.ServerProxy(server_url, allow_none=True)
        try:
            core.get_server_version()
        except:
            print _("pyLoadCore not running")
            exit()

        if add:
            core.add_package(add, [add])
            print _("Linklist added")

        if command == "pause":
            core.pause_server()
        elif command == "unpause":
            core.unpause_server()
        elif command == "kill":
            core.kill()
            exit()
        elif command == "queue":
            data = core.status_downloads()
            for download in data:
                print "%5d %s %s" % (int(download['id']),download['status'].rjust(8),download['name'])
            exit()
        elif command == "toggle":
            if core.status_server()['pause']:
                core.unpause_server()
            else:
                core.pause_server()
        elif command == "status":
            pass
        else:
            if command != "help": print _("Unknown Command")
            print _("Use one of:")

            commands = [(_("status"), _("prints server status")),
                        (_("queue"), _("prints download queue")),
                        (_("pause"), _("pause the server")),
                        (_("unpause"), _("continue downloads")),
                        (_("toggle"), _("toggle pause/unpause")),
                        (_("kill") , _("kill server")),]
            
            for c in commands:
                print "%-15s %s" % c

        print ""
        data = core.status_downloads()
        status = core.status_server()
        #Ausgabe generieren
        if status['pause']:
            print _('Status: paused')
        else:
            print _('Status: running')
        print _('%s Downloads') % len(data)
        for download in data:
            if download["status"] == 12: #downloading
                print _('Downloading: %(name)-40s %(percent)s%%  @%(speed)dkB/s') % download
            elif download["status"] == 5:
                print _("Waiting: %(name)s-40s: %(format_wait)s") % download


    else:
        cli = pyLoadCli(server_url)