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

from itertools import islice
from time import time

from Handler import Handler
from printer import *

from module.Api import Destination, PackageData

class ManageFiles(Handler):
    """ possibility to manage queue/collector """

    def init(self):
        self.target = Destination.Queue
        self.pos = 0    #position in queue
        self.package = -1  #choosen package
        self.mode = ""   # move/delete/restart

        self.cache = None
        self.links = None
        self.time = 0

    def onChar(self, char):
        if char in ("m", "d", "r"):
            self.mode = char
            self.setInput()
        elif char == "p":
            self.pos = max(0, self.pos - 5)
            self.backspace()
        elif char == "n":
            self.pos += 5
            self.backspace()

    def onBackSpace(self):
        if not self.input and self.mode:
            self.mode = ""
        if not self.input and self.package > -1:
            self.package = -1

    def onEnter(self, input):
        if input == "0":
            self.cli.reset()
        elif self.package < 0 and self.mode:
            #mode select
            packs = self.parseInput(input)
            if self.mode == "m":
                [self.client.movePackage((self.target + 1) % 2, x) for x in packs]
            elif self.mode == "d":
                self.client.deletePackages(packs)
            elif self.mode == "r":
                [self.client.restartPackage(x) for x in packs]

        elif self.mode:
            #edit links
            links = self.parseInput(input, False)

            if self.mode == "d":
                self.client.deleteFiles(links)
            elif self.mode == "r":
                map(self.client.restartFile, links)

        else:
            #look into package
            try:
                self.package = int(input)
            except:
                pass

        self.cache = None
        self.links = None
        self.pos = 0
        self.mode = ""
        self.setInput()


    def renderBody(self, line):
        if self.package < 0:
            println(line, white(_("Manage Packages:")))
        else:
            println(line, white((_("Manage Links:"))))
        line += 1

        if self.mode:
            if self.mode == "m":
                println(line, _("What do you want to move?"))
            elif self.mode == "d":
                println(line, _("What do you want to delete?"))
            elif self.mode == "r":
                println(line, _("What do you want to restart?"))

            println(line + 1, "Enter single number, comma seperated numbers or ranges. eg. 1,2,3 or 1-3.")
            line += 2
        else:
            println(line, _("Choose what yout want to do or enter package number."))
            println(line + 1, ("%s - %%s, %s - %%s, %s - %%s" % (mag("d"), mag("m"), mag("r"))) % (
            _("delete"), _("move"), _("restart")))
            line += 2

        if self.package < 0:
            #print package info
            pack = self.getPackages()
            i = 0
            for value in islice(pack, self.pos, self.pos + 5):
                try:
                    println(line, mag(str(value.pid)) + ": " + value.name)
                    line += 1
                    i += 1
                except Exception, e:
                    pass
            for x in range(5 - i):
                println(line, "")
                line += 1
        else:
            #print links info
            pack = self.getLinks()
            i = 0
            for value in islice(pack.links, self.pos, self.pos + 5):
                try:
                    println(line, mag(value.fid) + ": %s | %s | %s" % (
                    value.name, value.statusmsg, value.plugin))
                    line += 1
                    i += 1
                except Exception, e:
                    pass
            for x in range(5 - i):
                println(line, "")
                line += 1

        println(line, mag("p") + _(" - previous") + " | " + mag("n") + _(" - next"))
        println(line + 1, mag("0.") + _(" back to main menu"))

        return line + 2


    def getPackages(self):
        if self.cache and self.time + 2 < time():
            return self.cache

        if self.target == Destination.Queue:
            data = self.client.getQueue()
        else:
            data = self.client.getCollector()


        self.cache = data
        self.time = time()

        return data

    def getLinks(self):
        if self.links and self.time + 1 < time():
            return self.links

        try:
            data = self.client.getPackageData(self.package)
        except:
            data = PackageData(links=[])

        self.links = data
        self.time = time()

        return data

    def parseInput(self, inp, package=True):
        inp = inp.strip()
        if "-" in inp:
            l, n, h = inp.partition("-")
            l = int(l)
            h = int(h)
            r = range(l, h + 1)

            ret = []
            if package:
                for p in self.cache:
                    if p.pid in r:
                        ret.append(p.pid)
            else:
                for l in self.links.links:
                    if l.lid in r:
                        ret.append(l.lid)

            return ret

        else:
            return [int(x) for x in inp.split(",")]
