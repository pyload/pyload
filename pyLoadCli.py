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

    def data_arrived(self, obj):
        """Handle incoming data"""
        if obj.command == "update":
            print str(obj.data)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        address = raw_input("Adress:")
        port = raw_input("Port:")
        pw = raw_input("Password:")
        cli = pyLoadCli(adress,port,pw)
    else:
        cli = pyLoadCli(*sys.argv[1:])
        

