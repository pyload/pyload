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
        self.thread = SocketThread(adress, int(port), pw, self)
        self.getch = _Getch()
        self.input = ""
        self.pos = [0]
        self.inputline = 0
        self.menuline = 0

        os.system("clear")
        self.println(1, "pyLoad Command Line Interface")
        self.println(2, "")

        self.start()

    def start(self):
        while True:
            #inp = raw_input()
            inp = self.getch.impl()
            if ord(inp) == 3:
                os.system("clear")
                sys.exit() # ctrl + c
            elif ord(inp) == 13:
                self.handle_input()
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
        print "\033["+ str(line) +";0H\033[2K" + str(content) + "\033["+ str((self.inputline if self.inputline > 0 else self.inputline + 1) - 1) +";0H"

    def print_input(self):
        self.println(self.inputline," Input: " + self.input)

    def data_arrived(self, obj):
        """Handle incoming data"""
        if obj.command == "update":
            #print updated information
            self.println(1, "pyLoad Command Line Interface")
            self.println(2, "")
            self.println(3, "%s Downloads" % (len(obj.data)))
            line = 4
            speed = 0
            for download in obj.data:
                if download["status"] == "downloading":
                    percent = download["percent"]
                    z = percent / 4
                    speed += download['speed']
                    self.println(line, download["name"])
                    line += 1
                    self.println(line, "[" + z * "#" + (25-z) * " " + "] " + str(percent)+"% DL: "+str(int(download['speed']))+" kb/s  ETA: " +  self.format_time(download['eta']))
                    line += 1
                if download["status"] == "waiting":
                    self.println(line, download["name"])
                    line += 1
                    self.println(line, "waiting")
                    line += 1
            
            line += 1
            self.println(line, "Status: paused" if obj.status['pause'] else "Status: running" + " Speed: "+ str(int(speed))+" kb/s Files in queue: "+ str(obj.status["queue"]) )
            line += 1
            self.println(line, "")
            line += 1
            self.menuline = line
            
            self.build_menu()

    def build_menu(self):
        line = self.menuline
        self.println(line, "Menu:")
        line += 1 
        if self.pos[0] == 0:# main menu
            self.println(line, "1. Add Link")
            line += 1
            self.println(line, "2. Remove Link")
            line += 1
            self.println(line, "3. Pause Server")
            line += 1
            self.println(line, "4. Kill Server")
            line += 1
            self.println(line, "5. Quit")
            line += 1
      
        self.inputline = line +1
        self.print_input()

    def handle_input(self):
        input = self.input

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
