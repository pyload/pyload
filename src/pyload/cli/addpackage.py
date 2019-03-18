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

    def on_enter(self, inp):
        if inp == "0":
            self.cli.reset()

        if not self.name:
            self.name = inp
            self.set_input()
        elif inp == "END":
            # add package
            self.client.add_package(self.name, self.urls, 1)
            self.cli.reset()
        else:
            if inp.strip():
                self.urls.append(inp)
            self.set_input()

    def render_body(self, line):
        println(line, white("Add Package:"))
        println(line + 1, "")
        line += 2

        if not self.name:
            println(line, "Enter a name for the new package")
            println(line + 1, "")
            line += 2
        else:
            println(line, f"Package: {self.name}")
            println(line + 1, "Parse the links you want to add")
            println(line + 2, f"Type {mag('END')} when done")
            println(line + 3, f"Links added: mag(len(self.urls))")
            line += 4

        println(line, "")
        println(line + 1, mag("0.") + " back to main menu")

        return line + 2
