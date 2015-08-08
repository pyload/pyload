# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import time

from shutil import move

from module.plugins.internal.Addon import Addon
from module.utils import fs_encode, save_join as fs_join


class HotFolder(Addon):
    __name__    = "HotFolder"
    __type__    = "hook"
    __version__ = "0.16"
    __status__  = "testing"

    __config__ = [("folder"    , "str" , "Folder to observe"    , "container"),
                  ("watch_file", "bool", "Observe link file"    , False      ),
                  ("keep"      , "bool", "Keep added containers", True       ),
                  ("file"      , "str" , "Link file"            , "links.txt")]

    __description__ = """Observe folder and file for changes and add container and links"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.de")]


    def init(self):
        self.interval = 30


    def periodical(self):
        folder = fs_encode(self.get_config('folder'))
        file   = fs_encode(self.get_config('file'))

        try:
            if not os.path.isdir(os.path.join(folder, "finished")):
                os.makedirs(os.path.join(folder, "finished"))

            if self.get_config('watch_file'):
                with open(file, "a+") as f:
                    f.seek(0)
                    content = f.read().strip()

                if content:
                    f = open(file, "wb")
                    f.close()

                    name = "%s_%s.txt" % (file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(fs_join(folder, "finished", name), "wb") as f:
                        f.write(content)

                    self.pyload.api.addPackage(f.name, [f.name], 1)

            for f in os.listdir(folder):
                path = os.path.join(folder, f)

                if not os.path.isfile(path) or f.endswith("~") or f.startswith("#") or f.startswith("."):
                    continue

                newpath = os.path.join(folder, "finished", f if self.get_config('keep') else "tmp_" + f)
                move(path, newpath)

                self.log_info(_("Added %s from HotFolder") % f)
                self.pyload.api.addPackage(f, [newpath], 1)

        except (IOError, OSError), e:
            self.log_error(e)
