#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 RaNaN, Willnix
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
import os
import sys
import thread
import time

from module.remote.ClientSocket import SocketThread

class pyLoadCli:
    def __init__(self, adress, port, pw):
        os.system("clear")
        self.println(1, "pyLoad Command Line Interface")
        self.println(2, "")
        self.thread = SocketThread(adress, int(port), pw, self)
        self.getch = _Getch()
        self.input = ""
        self.inputline = 0
        self.start()

    def start(self):
        while True:
            #inp = raw_input()
            inp = self.getch.impl()
            if ord(inp) == 3:
                sys.exit() # ctrl + c
            elif ord(inp) == 13:
                self.input = ""   #enter
                self.println(self.inputline, self.input)
            elif ord(inp) == 127:
                self.input = self.input[:-1] #backspace
                self.println(self.inputline, self.input)
            else:
                self.input += inp
                self.println(self.inputline, self.input)

    def format_time(self, seconds):
        seconds = int(seconds)
        if seconds > 60:
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
        return _("%i seconds") % seconds

    def println(self, line, content):
        print "\033["+ str(line) +";0H" + str(content) + " " * 60


    def data_arrived(self, obj):
        """Handle incoming data"""
        if obj.command == "update":
            #print obj.data

            self.println(3, "%s Downloads" % (len(obj.data)))
            line = 4
            for download in obj.data:
                if download["status"] == "downloading":
                    percent = download["percent"]
                    z = percent / 2
                    print "\033[" + str(line) + ";0H[" + z * "#" + (50-z) * " " + "] " + str(percent) + "% of " + download["name"]
                    line += 1
            line += 2
            self.inputline = line + 2
            print("\033[" + str(line) + ";0HMeldungen:")
            for download in obj.data:
                if download["status"] == "waiting":
                    print "\033[" + str(line) + ";0HWarte %s auf Downlod Ticket für %s" % (self.format_time(download["wait_until"]), download["name"])
                    line += 1

class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
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


if __name__ == "__main__":
    if len(sys.argv) != 4:
        address = raw_input("Adress:")
        port = raw_input("Port:")
        password = raw_input("Password:")
        #address = "localhost"
        #port = "7272"
        #password = "pwhere"
        cli = pyLoadCli(address, port, password)
    else:
        cli = pyLoadCli( * sys.argv[1:])