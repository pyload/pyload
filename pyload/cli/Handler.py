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
class Handler:
    def __init__(self, cli):
        self.cli = cli
        self.init()

    client = property(lambda self: self.cli.client)
    input = property(lambda self: self.cli.input)

    def init(self):
        pass

    def onChar(self, char):
        pass

    def onBackSpace(self):
        pass

    def onEnter(self, inp):
        pass

    def setInput(self, inp=""):
        self.cli.setInput(inp)

    def backspace(self):
        self.cli.setInput(self.input[:-1])

    def renderBody(self, line):
        """ gets the line where to render output and should return the line number below its content """
        return line + 1