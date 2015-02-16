# -*- coding: utf-8 -*-

from __future__ import with_statement

import time

from os import listdir, makedirs
from os.path import exists, isfile, join
from shutil import move

from pyload.plugin.Addon import Addon
from pyload.utils import fs_encode, safe_join


class HotFolder(Addon):
    __name    = "HotFolder"
    __type    = "addon"
    __version = "0.12"

    __config = [("folder"    , "str" , "Folder to observe"    , "container"),
                ("watch_file", "bool", "Observe link file"    , False      ),
                ("keep"      , "bool", "Keep added containers", True       ),
                ("file"      , "str" , "Link file"            , "links.txt")]

    __description = """Observe folder and file for changes and add container and links"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.de")]


    def setup(self):
        self.interval = 10


    def activate(self):
        self.initPeriodical()


    def periodical(self):
        folder = fs_encode(self.getConfig("folder"))

        try:
            if not exists(join(folder, "finished")):
                makedirs(join(folder, "finished"))

            if self.getConfig("watch_file"):
                file = fs_encode(self.getConfig("file"))
                with open(file, "a+") as f:
                    content = f.read().strip()

                if content:
                    name = "%s_%s.txt" % (self.getConfig("file"), time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(safe_join(folder, "finished", name), "wb") as f:
                        f.write(content)

                    self.core.api.addPackage(f.name, [f.name], 1)

            for f in listdir(folder):
                path = join(folder, f)

                if not isfile(path) or f.endswith("~") or f.startswith("#") or f.startswith("."):
                    continue

                newpath = join(folder, "finished", f if self.getConfig("keep") else "tmp_" + f)
                move(path, newpath)

                self.logInfo(_("Added %s from HotFolder") % f)
                self.core.api.addPackage(f, [newpath], 1)

        except IOError, e:
            self.logError(e)
