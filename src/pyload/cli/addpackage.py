# -*- coding: utf-8 -*-
# AUTHOR: RaNaN


from .handler import Handler
from .printer import *


class AddPackage(Handler):
    """
    let the user add packages.
    """

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
            # add package
            self.client.addPackage(self.name, self.urls, 1)
            self.cli.reset()
        else:
            if inp.strip():
                self.urls.append(inp)
            self.setInput()

    def renderBody(self, line):
        println(line, white("Add Package:"))
        println(line + 1, "")
        line += 2

        if not self.name:
            println(line, "Enter a name for the new package")
            println(line + 1, "")
            line += 2
        else:
            println(line, "Package: {}".format(self.name))
            println(line + 1, "Parse the links you want to add.")
            println(line + 2, "Type {} when done.".format(mag("END")))
            println(line + 3, "Links added: " + mag(len(self.urls)))
            line += 4

        println(line, "")
        println(line + 1, mag("0.") + " back to main menu")

        return line + 2
