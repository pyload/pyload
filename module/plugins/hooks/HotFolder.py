# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import shutil
import time

from ..internal.Addon import Addon
from ..internal.misc import encode, fsjoin


class HotFolder(Addon):
    __name__ = "HotFolder"
    __type__ = "hook"
    __version__ = "0.24"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("folder", "str", "Folder to watch", "watchdir"),
                  ("watchfile", "bool", "Watch link file", False),
                  ("delete", "bool", "Delete added containers", False),
                  ("file", "str", "Link file", "links.txt")]

    __description__ = """Observe folder and file for changes and add container and links"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.de")]

    def activate(self):
        self.periodical.start(60, threaded=True)

    def periodical_task(self):
        folder = encode(self.config.get('folder'))
        file = encode(self.config.get('file'))

        try:
            if not os.path.isdir(os.path.join(folder, "finished")):
                os.makedirs(os.path.join(folder, "finished"))

            if self.config.get('watchfile'):
                with open(file, "a+") as f:
                    f.seek(0)
                    content = f.read().strip()

                if content:
                    f = open(file, "wb")
                    f.close()

                    name = "%s_%s.txt" % (
                        file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(fsjoin(folder, "finished", name), "wb") as f:
                        f.write(content)

                    self.pyload.api.addPackage(f.name, [f.name], 1)

            for f in os.listdir(folder):
                path = os.path.join(folder, f)

                if not os.path.isfile(path) or f.endswith(
                        "~") or f.startswith("#") or f.startswith("."):
                    continue

                newpath = os.path.join(
                    folder,
                    "finished",
                    "tmp_" +
                    f if self.config.get('delete') else f)
                shutil.move(path, newpath)

                self.log_info(_("Added %s from HotFolder") % f)
                self.pyload.api.addPackage(f, [newpath], 1)

        except (IOError, OSError), e:
            self.log_error(e, trace=True)
