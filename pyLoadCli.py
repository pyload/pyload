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
from __future__ import with_statement
from getopt import GetoptError, getopt

import module.common.pylgettext as gettext
import os
from os import _exit
from os.path import join, exists, abspath, basename
import sys
from sys import exit
from threading import Thread, Lock
from time import sleep
from traceback import print_exc

import ConfigParser

from codecs import getwriter

if os.name == "nt":
    enc = "cp850"
else:
    enc = "utf8"

sys.stdout = getwriter(enc)(sys.stdout, errors="replace")

from module import InitHomeDir
from module.cli.printer import *
from module.cli import AddPackage, ManageFiles

from module.Api import Destination
from module.utils import formatSize, decode
from module.remote.thriftbackend.ThriftClient import ThriftClient, NoConnection, NoSSL, WrongLogin, ConnectionClosed
from module.lib.Getch import Getch
from module.lib.rename_process import renameProcess

class Cli:
    def __init__(self, client, command):
        self.client = client
        self.command = command

        if not self.command:
            renameProcess('pyLoadCli')
            self.getch = Getch()
            self.input = ""
            self.inputline = 0
            self.lastLowestLine = 0
            self.menuline = 0

            self.lock = Lock()

            #processor funcions, these will be changed dynamically depending on control flow
            self.headerHandler = self   #the download status
            self.bodyHandler = self    #the menu section
            self.inputHandler = self

            os.system("clear")
            println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
            println(2, "")

            self.thread = RefreshThread(self)
            self.thread.start()

            self.start()
        else:
            self.processCommand()

    def reset(self):
        """ reset to initial main menu """
        self.input = ""
        self.headerHandler = self.bodyHandler = self.inputHandler = self

    def start(self):
        """ main loop. handle input """
        while True:
            #inp = raw_input()
            inp = self.getch.impl()
            if ord(inp) == 3:
                os.system("clear")
                sys.exit() # ctrl + c
            elif ord(inp) == 13: #enter
                try:
                    self.lock.acquire()
                    self.inputHandler.onEnter(self.input)

                except Exception, e:
                    println(2, red(e))
                finally:
                    self.lock.release()

            elif ord(inp) == 127:
                self.input = self.input[:-1] #backspace
                try:
                    self.lock.acquire()
                    self.inputHandler.onBackSpace()
                finally:
                    self.lock.release()

            elif ord(inp) == 27: #ugly symbol
                pass
            else:
                self.input += inp
                try:
                    self.lock.acquire()
                    self.inputHandler.onChar(inp)
                finally:
                    self.lock.release()

            self.inputline = self.bodyHandler.renderBody(self.menuline)
            self.renderFooter(self.inputline)


    def refresh(self):
        """refresh screen"""

        println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
        println(2, "")

        self.lock.acquire()

        self.menuline = self.headerHandler.renderHeader(3) + 1
        println(self.menuline - 1, "")
        self.inputline = self.bodyHandler.renderBody(self.menuline)
        self.renderFooter(self.inputline)

        self.lock.release()


    def setInput(self, string=""):
        self.input = string

    def setHandler(self, klass):
        #create new handler with reference to cli
        self.bodyHandler = self.inputHandler = klass(self)
        self.input = ""

    def renderHeader(self, line):
        """ prints download status """
        #print updated information
        #        print "\033[J" #clear screen
        #        self.println(1, blue("py") + yellow("Load") + white(_(" Command Line Interface")))
        #        self.println(2, "")
        #        self.println(3, white(_("%s Downloads:") % (len(data))))

        data = self.client.statusDownloads()
        speed = 0

        println(line, white(_("%s Downloads:") % (len(data))))
        line += 1

        for download in data:
            if download.status == 12:  # downloading
                percent = download.percent
                z = percent / 4
                speed += download.speed
                println(line, cyan(download.name))
                line += 1
                println(line,
                    blue("[") + yellow(z * "#" + (25 - z) * " ") + blue("] ") + green(str(percent) + "%") + _(
                        " Speed: ") + green(formatSize(download.speed) + "/s") + _(" Size: ") + green(
                        download.format_size) + _(" Finished in: ") + green(download.format_eta) + _(
                        " ID: ") + green(download.fid))
                line += 1
            if download.status == 5:
                println(line, cyan(download.name))
                line += 1
                println(line, _("waiting: ") + green(download.format_wait))
                line += 1

        println(line, "")
        line += 1
        status = self.client.statusServer()
        if status.pause:
            paused = _("Status:") + " " + red(_("paused"))
        else:
            paused = _("Status:") + " " + red(_("running"))

        println(line,"%s %s: %s %s: %s %s: %s" % (
            paused, _("total Speed"), red(formatSize(speed) + "/s"), _("Files in queue"), red(
                status.queue), _("Total"), red(status.total)))

        return line + 1

    def renderBody(self, line):
        """ prints initial menu """
        println(line, white(_("Menu:")))
        println(line + 1, "")
        println(line + 2, mag("1.") + _(" Add Links"))
        println(line + 3, mag("2.") + _(" Manage Queue"))
        println(line + 4, mag("3.") + _(" Manage Collector"))
        println(line + 5, mag("4.") + _(" (Un)Pause Server"))
        println(line + 6, mag("5.") + _(" Kill Server"))
        println(line + 7, mag("6.") + _(" Quit"))

        return line + 8

    def renderFooter(self, line):
        """ prints out the input line with input """
        println(line, "")
        line += 1

        println(line, white(" Input: ") + decode(self.input))

        #clear old output
        if line < self.lastLowestLine:
            for i in range(line + 1, self.lastLowestLine + 1):
                println(i, "")

        self.lastLowestLine = line

        #set cursor to position
        print "\033[" + str(self.inputline) + ";0H"

    def onChar(self, char):
        """ default no special handling for single chars """
        if char == "1":
            self.setHandler(AddPackage)
        elif char == "2":
            self.setHandler(ManageFiles)
        elif char == "3":
            self.setHandler(ManageFiles)
            self.bodyHandler.target = Destination.Collector
        elif char == "4":
            self.client.togglePause()
            self.setInput()
        elif char == "5":
            self.client.kill()
            self.client.close()
            sys.exit()
        elif char == "6":
            os.system('clear')
            sys.exit()

    def onEnter(self, inp):
        pass

    def onBackSpace(self):
        pass

    def processCommand(self):
        command = self.command[0]
        args = []
        if len(self.command) > 1:
            args = self.command[1:]

        if command == "status":
            files = self.client.statusDownloads()

            if not files:
                print "No downloads running."

            for download in files:
                if download.status == 12:  # downloading
                    print print_status(download)
                    print "\tDownloading: %s @ %s/s\t %s (%s%%)" % (
                        download.format_eta, formatSize(download.speed), formatSize(download.size - download.bleft),
                        download.percent)
                elif download.status == 5:
                    print print_status(download)
                    print "\tWaiting: %s" % download.format_wait
                else:
                    print print_status(download)

        elif command == "queue":
            print_packages(self.client.getQueueData())

        elif command == "collector":
            print_packages(self.client.getCollectorData())

        elif command == "add":
            if len(args) < 2:
                print _("Please use this syntax: add <Package name> <link> <link2> ...")
                return

            self.client.addPackage(args[0], args[1:], Destination.Queue)

        elif command == "add_coll":
            if len(args) < 2:
                print _("Please use this syntax: add <Package name> <link> <link2> ...")
                return

            self.client.addPackage(args[0], args[1:], Destination.Collector)

        elif command == "del_file":
            self.client.deleteFiles([int(x) for x in args])
            print "Files deleted."

        elif command == "del_package":
            self.client.deletePackages([int(x) for x in args])
            print "Packages deleted."

        elif command == "move":
            for pid in args:
                pack = self.client.getPackageInfo(int(pid))
                self.client.movePackage((pack.dest + 1) % 2, pack.pid)

        elif command == "check":
            print _("Checking %d links:") % len(args)
            print
            rid = self.client.checkOnlineStatus(args).rid
            self.printOnlineCheck(self.client, rid)


        elif command == "check_container":
            path = args[0]
            if not exists(join(owd, path)):
                print _("File does not exists.")
                return

            f = open(join(owd, path), "rb")
            content = f.read()
            f.close()

            rid = self.client.checkOnlineStatusContainer([], basename(f.name), content).rid
            self.printOnlineCheck(self.client, rid)


        elif command == "pause":
            self.client.pause()

        elif command == "unpause":
            self.client.unpause()

        elif command == "toggle":
            self.client.togglePause()

        elif command == "kill":
            self.client.kill()
        elif command == "restart_file":
            for x in args:
                self.client.restartFile(int(x))
            print "Files restarted."
        elif command == "restart_package":
            for pid in args:
                self.client.restartPackage(int(pid))
            print "Packages restarted."

        else:
            print_commands()

    def printOnlineCheck(self, client, rid):
        while True:
            sleep(1)
            result = client.pollResults(rid)
            for url, status in result.data.iteritems():
                if status.status == 2: check = "Online"
                elif status.status == 1: check = "Offline"
                else: check = "Unknown"

                print "%-45s %-12s\t %-15s\t %s" % (status.name, formatSize(status.size), status.plugin, check)

            if result.rid == -1: break


class RefreshThread(Thread):
    def __init__(self, cli):
        Thread.__init__(self)
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
                println(2, red(str(e)))
                self.cli.reset()
                print_exc()


def print_help(config):
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
    print "  -u, --username=", " " * 2, "Specify Username"
    print "  --pw=<password>", " " * 2, "Password"
    print "  -a, --address=", " " * 3, "Specify address (current=%s)" % config["addr"]
    print "  -p, --port", " " * 7, "Specify port (current=%s)" % config["port"]
    print
    print "  -l, --language", " " * 3, "Set user interface language (current=%s)" % config["language"]
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
        ("add_coll <name> <link1> <link2>...", _("Adds package to collector")),
        ("del_file <fid> <fid2>...", _("Delete Files from Queue/Collector")),
        ("del_package <pid> <pid2>...", _("Delete Packages from Queue/Collector")),
        ("move <pid> <pid2>...", _("Move Packages from Queue to Collector or vice versa")),
        ("restart_file <fid> <fid2>...", _("Restart files")),
        ("restart_package <pid> <pid2>...", _("Restart packages")),
        ("check <container|url> ...", _("Check online status, works with local container")),
        ("check_container path", _("Checks online status of a container file")),
        ("pause", _("Pause the server")),
        ("unpause", _("continue downloads")),
        ("toggle", _("Toggle pause/unpause")),
        ("kill", _("kill server")), ]

    print _("List of commands:")
    print
    for c in commands:
        print "%-35s %s" % c


def writeConfig(opts):
    try:
        with open(join(homedir, ".pyloadcli"), "w") as cfgfile:
            cfgfile.write("[cli]")
            for opt in opts:
                cfgfile.write("%s=%s\n" % (opt, opts[opt]))
    except:
        print _("Couldn't write user config file")


def main():
    config = {"addr": "127.0.0.1", "port": "7227", "language": "en"}
    try:
        config["language"] = os.environ["LANG"][0:2]
    except:
        pass

    if (not exists(join(pypath, "locale", config["language"]))) or config["language"] == "":
        config["language"] = "en"

    configFile = ConfigParser.ConfigParser()
    configFile.read(join(homedir, ".pyloadcli"))

    if configFile.has_section("cli"):
        for opt in configFile.items("cli"):
            config[opt[0]] = opt[1]

    gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
    translation = gettext.translation("pyLoadCli", join(pypath, "locale"),
        languages=[config["language"],"en"],fallback=True)
    translation.install(unicode=True)

    interactive = False
    command = None
    username = ""
    password = ""

    shortOptions = 'iu:p:a:hcl:'
    longOptions = ['interactive', "username=", "pw=", "address=", "port=", "help", "commands", "language="]

    try:
        opts, extraparams = getopt(sys.argv[1:], shortOptions, longOptions)
        for option, params in opts:
            if option in ("-i", "--interactive"):
                interactive = True
            elif option in ("-u", "--username"):
                username = params
            elif option in ("-a", "--address"):
                config["addr"] = params
            elif option in ("-p", "--port"):
                config["port"] = params
            elif option in ("-l", "--language"):
                config["language"] = params
                gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
                translation = gettext.translation("pyLoadCli", join(pypath, "locale"),
                    languages=[config["language"],"en"],fallback=True)
                translation.install(unicode=True)
            elif option in ("-h", "--help"):
                print_help(config)
                exit()
            elif option in ("--pw"):
                password = params
            elif option in ("-c", "--comands"):
                print_commands()
                exit()

    except GetoptError:
        print 'Unknown Argument(s) "%s"' % " ".join(sys.argv[1:])
        print_help(config)
        exit()

    if len(extraparams) >= 1:
        command = extraparams

    client = False

    if interactive:
        try:
            client = ThriftClient(config["addr"], int(config["port"]), username, password)
        except WrongLogin:
            pass
        except NoSSL:
            print _("You need py-openssl to connect to this pyLoad Core.")
            exit()
        except NoConnection:
            config["addr"] = False
            config["port"] = False

        if not client:
            if not config["addr"]: config["addr"] = raw_input(_("Address: "))
            if not config["port"]: config["port"] = raw_input(_("Port: "))
            if not username: username = raw_input(_("Username: "))
            if not password:
                from getpass import getpass

                password = getpass(_("Password: "))

            try:
                client = ThriftClient(config["addr"], int(config["port"]), username, password)
            except WrongLogin:
                print _("Login data is wrong.")
            except NoConnection:
                print _("Could not establish connection to %(addr)s:%(port)s." % {"addr": config["addr"],
                                                                                  "port": config["port"]})

    else:
        try:
            client = ThriftClient(config["addr"], int(config["port"]), username, password)
        except WrongLogin:
            print _("Login data is wrong.")
        except NoConnection:
            print _("Could not establish connection to %(addr)s:%(port)s." % {"addr": config["addr"],
                                                                              "port": config["port"]})
        except NoSSL:
            print _("You need py-openssl to connect to this pyLoad core.")

    if interactive and command: print _("Interactive mode ignored since you passed some commands.")

    if client:
        writeConfig(config)
        cli = Cli(client, command)


if __name__ == "__main__":
    main()
