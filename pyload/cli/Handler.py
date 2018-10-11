# -*- coding: utf-8 -*-
from builtins import _
# @author: RaNaN

from builtins import _, object


class Handler(object):
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
