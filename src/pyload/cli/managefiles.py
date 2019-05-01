# -*- coding: utf-8 -*-
# AUTHOR: RaNaN

import time
from itertools import islice

from pyload.core.datatypes.data import PackageData
from pyload.core.datatypes.enums import Destination

from .handler import Handler
from .printer import *


class ManageFiles(Handler):
    """
    possibility to manage queue/collector.
    """

    def init(self):
        self.target = Destination.QUEUE
        self.pos = 0  #: position in queue
        self.package = -1  #: choosen package
        self.mode = ""  #: move/delete/restart

        self.cache = None
        self.links = None
        self.time = 0

    def on_char(self, char):
        if char in ("m", "d", "r"):
            self.mode = char
            self.set_input()
        elif char == "p":
            self.pos = max(0, self.pos - 5)
            self.backspace()
        elif char == "n":
            self.pos += 5
            self.backspace()

    def on_back_space(self):
        if not self.input and self.mode:
            self.mode = ""
        if not self.input and self.package > -1:
            self.package = -1

    def on_enter(self, input):
        if input == "0":
            self.cli.reset()
        elif self.package < 0 and self.mode:
            # mode select
            packs = self.parse_input(input)
            if self.mode == "m":
                [self.client.move_package((self.target + 1) % 2, x) for x in packs]
            elif self.mode == "d":
                self.client.delete_packages(packs)
            elif self.mode == "r":
                [self.client.restart_package(x) for x in packs]

        elif self.mode:
            # edit links
            links = self.parse_input(input, False)

            if self.mode == "d":
                self.client.delete_files(links)
            elif self.mode == "r":
                for link in links:
                    self.client.restart_file(link)

        else:
            # look into package
            try:
                self.package = int(input)
            except Exception:
                pass

        self.cache = None
        self.links = None
        self.pos = 0
        self.mode = ""
        self.set_input()

    def render_body(self, line):
        if self.package < 0:
            println(line, white("Manage Packages:"))
        else:
            println(line, white(("Manage Links:")))
        line += 1

        if self.mode:
            if self.mode == "m":
                println(line, "What do you want to move?")
            elif self.mode == "d":
                println(line, "What do you want to delete?")
            elif self.mode == "r":
                println(line, "What do you want to restart?")

            println(
                line + 1,
                "Enter single number, comma seperated numbers or ranges. eg. 1,2,3 or 1-3.",
            )
            line += 2
        else:
            println(line, "Choose what you want to do or enter package number.")
            println(
                line + 1, f"{mag('d')} - delete, mag('m') - move, mag('r') - restart"
            )
            line += 2

        if self.package < 0:
            # print(package info)
            pack = self.get_packages()
            i = 0
            for value in islice(pack, self.pos, self.pos + 5):
                try:
                    println(line, mag(str(value.pid)) + ": " + value.name)
                    line += 1
                    i += 1
                except Exception:
                    pass
            for x in range(5 - i):
                println(line, "")
                line += 1
        else:
            # print(links info)
            pack = self.get_links()
            i = 0
            for value in islice(pack.links, self.pos, self.pos + 5):
                try:
                    println(
                        line,
                        mag(value.fid)
                        + f": {value.name} | {value.statusmsg} | {value.plugin}",
                    )
                    line += 1
                    i += 1
                except Exception:
                    pass
            for x in range(5 - i):
                println(line, "")
                line += 1

        println(line, mag("p") + " - previous" + " | " + mag("n") + " - next")
        println(line + 1, mag("0.") + " back to main menu")

        return line + 2

    def get_packages(self):
        if self.cache and self.time + 2 < time.time():
            return self.cache

        if self.target == Destination.QUEUE:
            data = self.client.get_queue()
        else:
            data = self.client.get_collector()

        self.cache = data
        self.time = time.time()

        return data

    def get_links(self):
        if self.links and self.time + 1 < time.time():
            return self.links

        try:
            data = self.client.get_package_data(self.package)
        except Exception:
            data = PackageData(links=[])

        self.links = data
        self.time = time.time()

        return data

    def parse_input(self, inp, package=True):
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
