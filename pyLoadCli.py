#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2011 RaNaN
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
from getopt import GetoptError, getopt

import gettext
from itertools import islice
import os
from os import _exit
from os.path import join
import sys
from sys import exit
import threading
from time import sleep
from traceback import print_exc

from codecs import getwriter

sys.stdout = getwriter("utf8")(sys.stdout, errors="replace")

from module import InitHomeDir
from module.utils import formatSize, decode
from module.ConfigParser import ConfigParser
from module.remote.thriftbackend.ThriftClient import ThriftClient, NoConnection, NoSSL, WrongLogin, PackageDoesNotExists, ConnectionClosed

class Cli:
    def __init__(self, client, command):
        self.client = client
        self.command = command

        if not self.command:
            self.getch = _Getch()
            self.input = ""
            self.pos = [0, 0, 0]
            self.inputline = 0
            self.menuline = 0

            self.new_package = {}

            self.links_added = 0

            os.system("clear")
            self.println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
            self.println(2, "")

            self.file_list = {}

            self.thread = RefreshThread(self)
            self.thread.start()

            self.start()
        else:
            self.processCommand()

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
                    self.println(2, red(e))
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

    def println(self, line, content):
        print "\033[" + str(line) + ";0H\033[2K" + content + "\033[" + \
              str((self.inputline if self.inputline > 0 else self.inputline + 1) - 1) + ";0H"

    def print_input(self):
        self.println(self.inputline, white(" Input: ") + decode(self.input))
        self.println(self.inputline + 1, "")
        self.println(self.inputline + 2, "")
        self.println(self.inputline + 3, "")
        self.println(self.inputline + 4, "")

    def refresh(self):
        """Handle incoming data"""
        data = self.client.statusDownloads()
        #print updated information
        print "\033[J" #clear screen
        self.println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
        self.println(2, "")
        self.println(3, white(_("%s Downloads:") % (len(data))))
        line = 4
        speed = 0
        for download in data:
            if download.status == 12:  # downloading
                percent = download.percent
                z = percent / 4
                speed += download.speed
                self.println(line, cyan(download.name))
                line += 1
                self.println(line,
                             blue("[") + yellow(z * "#" + (25 - z) * " ") + blue("] ") + green(str(percent) + "%") + _(
                                     " Speed: ") + green(formatSize(speed)+ "/s") + _(" Size: ") + green(
                                     download.format_size) + _(" Finished in: ") + green(download.format_eta) + _(
                                     " ID: ") + green(download.fid))
                line += 1
            if download.status == 5:
                self.println(line, cyan(download.name))
                line += 1
                self.println(line, _("waiting: ") + green(download.format_wait))
                line += 1
        self.println(line, "")
        line += 1
        status = self.client.statusServer()
        if status.pause:
            self.println(line,
                         _("Status: ") + red("paused") + _(" total Speed: ") + red(formatSize(speed)+ "/s") + _(
                                 " Files in queue: ") + red(status.queue))
        else:
            self.println(line,
                         _("Status: ") + red("running") + _(" total Speed: ") + red(formatSize(speed) + "/s") + _(
                                 " Files in queue: ") + red(status.queue))
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
        if not self.pos[0]:# main menu
            self.println(line, "")
            line += 1
            self.println(line, mag("1.") + _(" Add Links"))
            line += 1
            self.println(line, mag("2.") + _(" Manage Links"))
            line += 1
            self.println(line, mag("3.") + _(" Manage Collector"))
            line += 1
            self.println(line, mag("4.") + _(" (Un)Pause Server"))
            line += 1
            self.println(line, mag("5.") + _(" Kill Server"))
            line += 1
            self.println(line, mag("6.") + _(" Quit"))
            line += 1
            self.println(line, "")
            line += 1
            self.println(line, "")
        elif self.pos[0] == 1:#add links

            if not self.pos[1]:
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
                self.println(line, _("Links added: ") + mag(self.links_added))
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, "")
                line += 1
                self.println(line, mag("0.") + _(" back to main menu"))
                line += 1
                self.println(line, "")
        elif self.pos[0] == 2 or self.pos[0] == 3: #Manage Queues
            swapdest = "Collector" if self.pos[0] == 2 else "Queue"
            if not self.pos[1]:
                if self.pos[0] == 2:
                    pack = self.client.getQueue()
                else:
                    pack = self.client.getCollector()
                self.println(line, _(
                        "Type d(number of package) to delete a package, r to restart, s to send to %s or w/o d,r,s to look into it." % swapdest))
                line += 1
                i = 0
                for value in islice(pack, self.pos[2], self.pos[2] + 5):
                    try:
                        self.println(line, mag(str(value.pid)) + ": " + value.name)
                        line += 1
                        i += 1
                    except Exception, e:
                        pass
                for x in range(5 - i):
                    self.println(line, "")
                    line += 1

            else:
                try:
                    pack = self.client.getPackageData(self.pos[1])
                except PackageDoesNotExists:
                    self.pos[1] = 0
                    self.print_input()
                    return
                    
                self.println(line, _("Type d(number) of the link you want to delete, r(number) to restart, s(number) to send to %s." % swapdest))
                line += 1
                i = 0
                for value in islice(pack.links, self.pos[2], self.pos[2] + 5):
                    try:
                        self.println(line, mag(value.fid) + ": %s | %s | %s" % (
                        value.name, value.statusmsg, value.plugin))
                        line += 1
                        i += 1

                    except Exception, e:
                        pass
                for x in range(5 - i):
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

        if not self.pos[0]:
            if inp == "1":
                self.links_added = 0
                self.pos[0] = 1
            elif inp == "2" or inp == "3":
                self.pos[0] = int(inp)
                self.pos[1] = 0
            elif inp == "4":
                self.client.togglePause()
            elif inp == "5":
                self.client.kill()
                self.client.close()
                sys.exit()
            elif inp == "6":
                os.system('clear')
                sys.exit()

        elif self.pos[0] == 1: #add links
            if not self.pos[1]:
                self.new_package['name'] = inp
                self.new_package['links'] = []
                self.pos[1] = 1
            else:
                if inp == "END":
                    self.client.addPackage(self.new_package['name'], self.new_package['links'], 1) # add package
                    self.pos = [0, 0, 0]
                    self.links_added = 0
                else: #TODO validation
                    self.new_package['links'].append(inp)
                    self.links_added += 1

        elif self.pos[0] == 2 or self.pos[0] == 3: #Manage queue/collector
            if not self.pos[1]:
                if inp.startswith("d"):
                    if inp.find("-") > -1:
                        self.client.deletePackages(range(*map(int, inp[1:].split("-"))))
                    else:
                        self.client.deletePackages([int(inp[1:])])
                elif inp.startswith("r"):
                    self.client.restartPackage(int(inp[1:]))
                elif inp.startswith("s"):
                    self.client.movePackage(int(self.pos[0])-2,int(inp[1:])) # Opt 3-2 == 1 (queue) Opt 2-2 == 0 (collector)
                elif inp != "p" and inp != "n":
                    self.pos[1] = int(inp)
                    self.pos[2] = 0
            elif inp.startswith('r'):
                if inp.find("-") > -1:
                    map(self.client.restartFile, range(*map(int, inp[1:].split("-"))))
                else:
                    self.client.restartFile(int(inp[1:]))
            elif inp.startswith("s"):
                self.client.movePackage(int(self.pos[0])-2,int(inp[1:])) # Opt 3-2 == 1 (queue) Opt 2-2 == 0 (collector)
            elif inp.startswith('d'):
                if inp.find("-") > -1:
                    self.client.deleteFiles(range(*map(int, inp[1:].split("-"))))
                else:
                    self.client.deleteFiles([int(inp[1:])])
            if inp == "p":
                self.pos[2] -= 5
            elif inp == "n":
                self.pos[2] += 5

        self.build_menu()

    def processCommand(self):
        command = self.command[0]
        args = []
        if len(self.command) > 1:
            args = self.command[1:]

        if command == "status":
            files = self.client.statusDownloads()

            for download in files:
                if download.status == 12:  # downloading
                    print print_status(download)
                    print "\tDownloading: %s @ %s/s\t %s (%s%%)" % (download.format_eta, formatSize(download.speed), formatSize(download.size - download.bleft), download.percent)
                if download.status == 5:
                    print print_status(download)
                    print "\tWaiting: %s" % download.format_wait

        elif command == "queue":
            print_packages(self.client.getQueueData())

        elif command == "collector":
            print_packages(self.client.getCollectorData())

        elif command == "add":
            if len(args) < 2:
                print _("Please use this syntax: add <Package name> <link> <link2> ...")
                return

            self.client.addPackage(args[0], args[1:], 1)

        elif command == "del_file":
            self.client.deleteFiles([int(x) for x in args])
            print "Files deleted."

        elif command == "del_package":
            self.client.deletePackages([int(x) for x in args])
            print "Packages deleted."

        elif command == "pause":
            self.client.pause()

        elif command == "unpause":
            self.client.unpause()

        elif command == "toggle":
            self.client.togglePause()

        elif command == "kill":
            self.client.kill()
        else:
            print_commands()


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
            except ConnectionClosed:
                os.system("clear")
                print _("pyLoad was terminated")
                _exit(0)
            except Exception, e:
                self.cli.println(2, red(str(e)))
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
    return "\033[1;34m" + unicode(string) + "\033[0m"

def green(string):
    return "\033[1;32m" + unicode(string) + "\033[0m"

def yellow(string):
    return "\033[1;33m" + unicode(string) + "\033[0m"

def red(string):
    return "\033[1;31m" + unicode(string) + "\033[0m"

def cyan(string):
    return "\033[1;36m" + unicode(string) + "\033[0m"

def mag(string):
    return "\033[1;35m" + unicode(string) + "\033[0m"

def white(string):
    return "\033[1;37m" + unicode(string) + "\033[0m"

def print_help():
    print
    print "pyLoadCli Copyright (c) 2008-2011 the pyLoad Team"
    print
    print "Usage: [python] pyLoadCli.py [options] [command]"
    print
    print "<Commands>"
    print "See pyLoadCli.py -c for a complete listing."
    print
    print "<Options>"
    print "  -i, --interactive", " Start in interactive mode" 
    print 
    print "  -u, --username=", " " * 2,  "Specify Username"
    print "  --pw=<password>", " " * 2, "Password"
    print "  -a, --address=", " "*3, "Specify address (default=127.0.0.1)"
    print "  -p, --port", " " * 7, "Specify port (default=7227)"
    print
    print "  -h, --help", " " * 7, "Display this help screen"
    print "  -c, --commands", " " * 3, "List all available commands"
    print


def print_packages(data):
    for pack in data:
        print "Package %s (#%s):" % (pack.name, pack.pid)
        for download in pack.links:
                print "\t" + print_file(download)
        print

def print_file(download):
    return "#%(id)-6d %(name)-30s %(statusmsg)-10s %(plugin)-8s" % {
                    "id": download.fid,
                    "name": download.name,
                    "statusmsg": download.statusmsg,
                    "plugin": download.plugin
                }

def print_status(download):
    return "#%(id)-6s %(name)-40s Status: %(statusmsg)-10s Size: %(size)s" % {
                    "id": download.fid,
                    "name": download.name,
                    "statusmsg": download.statusmsg,
                    "size": download.format_size
        }

def print_commands():
    commands = [("status", _("Prints server status")),
                ("queue", _("Prints downloads in queue")),
                ("collector", _("Prints downloads in collector")),
                ("add <name> <link1> <link2>...", _("Adds package to queue")),
                ("del_file <fid> <fid2>...", _("Delete Files from Queue/Collector")),
                ("del_package <pid> <pid2>...", _("Delete Packages from Queue/Collector")),
                ("pause", _("Pause the server")),
                ("unpause", _("continue downloads")),
                ("toggle", _("Toggle pause/unpause")),
                ("kill", _("kill server")), ]

    print _("List of commands:")
    print
    for c in commands:
        print "%-30s %s" % c

if __name__ == "__main__":
    config = ConfigParser()

    translation = gettext.translation("pyLoadCli", join(pypath, "locale"),
                                      languages=["en", config['general']['language']])
    translation.install(unicode=True)

    username = ""
    password = ""
    addr = "127.0.0.1"
    port = 7227

    interactive = False
    command = None

    shortOptions = 'iu:p:a:hc'
    longOptions = ['interactive', "username=", "pw=", "address=", "port=", "help", "commands"]

    try:
        opts, extraparams = getopt(sys.argv[1:], shortOptions, longOptions)
        for option, params in opts:
            if option in ("-i", "--interactive"):
                interactive = True
            elif option in ("-u", "--username"):
                username = params
            elif option in ("-a", "--address"):
                addr = params
            elif option in ("-p", "--port"):
                port = int(params)
            elif option in ("-h", "--help"):
                print_help()
                exit()
            elif option in ("--pw"):
                password = params
            elif option in ("-c", "--comands"):
                print_commands()
                exit()

    except GetoptError:
        print 'Unknown Argument(s) "%s"' % " ".join(sys.argv[1:])
        print_help()
        exit()

    if len(extraparams) >= 1:
        command = extraparams

    client = False

    if interactive:

        try:
            client = ThriftClient(addr, port, username, password)
        except WrongLogin:
            pass
        except NoSSL:
            print _("You need py-openssl to connect to this pyLoad Core.")
            exit()
        except NoConnection:
            addr = False
            port = False

        if not client:
            if not addr: addr = raw_input(_("Address: "))
            if not port: port = int(raw_input(_("Port: ")))
            if not username: username = raw_input(_("Username: "))
            if not password:
                from getpass import getpass

                password = getpass(_("Password: "))

            try:
                client = ThriftClient(addr, port, username, password)
            except WrongLogin:
                print _("Login data is wrong.")
            except NoConnection:
                print _("Could not establish connection to %(addr)s:%(port)s." % {"addr": addr, "port" : port })

    else:
        try:
            client = ThriftClient(addr, port, username, password)
        except WrongLogin:
            print _("Login data is required.")
        except NoConnection:
            print _("Could not establish connection to %(addr)s:%(port)s." % {"addr": addr, "port" : port })
        except NoSSL:
            print _("You need py-openssl to connect to this pyLoad.")


    if interactive and command: print _("Interactive mode ignored since you passed some commands.")

    if client:
        cli = Cli(client, command)
