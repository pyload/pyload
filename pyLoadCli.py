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
import time
import thread
import os
import sys
from module.remote.ClientSocket import SocketThread

class pyLoadCli:
    def __init__(self, adress, port, pw):
        thread = SocketThread(adress, int(port), pw, self)
        self.start()

    def start(self):
        while True:
            inp = raw_input()
            print inp[-1]

    def format_time(self, seconds):
        seconds = int(seconds)
        if seconds > 60:
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
        return _("%i seconds") % seconds

    def data_arrived(self, obj):
        """Handle incoming data"""
        if obj.command == "update":
            #print obj.data
            print "\033[2;0H%s Downloads" % (len(obj.data))
            line = 2
            for download in obj.data:
                if download["status"] == "downloading":
                    percent = download["percent"]
                    z = percent/2
                    print "\033["+str(line)+";0H[" + z*"#" + (50-z)*" " + "] " + str(percent) + "% of " + download["name"]
                    line += 1
            line += 2
            print("\033[" + str(line) + ";0HMeldungen:")
            for download in obj.data:
                if download["status"] == "waiting":
                    print "\033["+str(line)+";0HWarte %s auf Downlod Ticket für %s" % (self.format_time(download["wait_until"]), download["name"])
                    line += 1

if __name__ == "__main__":
    if len(sys.argv) != 4:
        address = raw_input("Adress:")
        port = raw_input("Port:")
        password = raw_input("Password:")
        #address = "localhost"
        #port = "7272"
        #password = "pwhere"
        cli = pyLoadCli(address,port,password)
    else:
        cli = pyLoadCli(*sys.argv[1:])
