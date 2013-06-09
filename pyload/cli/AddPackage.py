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

from Handler import Handler
from printer import *

class AddPackage(Handler):
    """ let the user add packages """

    def init(self):
        self.name = ""
        self.urls = []

    def onEnter(self, inp):
        if inp == "0":
            self.cli.reset()

        if not self.name:
            self.name = inp
            self.setInput()
        elif inp == "END":
            #add package
            self.client.addPackage(self.name, self.urls, 1)
            self.cli.reset()
        else:
            if inp.strip():
                self.urls.append(inp)
            self.setInput()

    def renderBody(self, line):
        println(line, white(_("Add Package:")))
        println(line + 1, "")
        line += 2

        if not self.name:
            println(line, _("Enter a name for the new package"))
            println(line + 1, "")
            line += 2
        else:
            println(line, _("Package: %s") % self.name)
            println(line + 1, _("Parse the links you want to add."))
            println(line + 2, _("Type %s when done.") % mag("END"))
            println(line + 3, _("Links added: ") + mag(len(self.urls)))
            line += 4

        println(line, "")
        println(line + 1, mag("0.") + _(" back to main menu"))

        return line + 2