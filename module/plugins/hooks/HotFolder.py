# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import shutil
import time

from ..internal.Addon import Addon
from ..internal.misc import fs_encode, fsjoin


class HotFolder(Addon):
    __name__ = "HotFolder"
    __type__ = "hook"
    __version__ = "0.27"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("folder", "folder", "Folder to watch", "watchdir"),
                  ("watchfile", "bool", "Watch link file", False),
                  ("delete", "bool", "Delete added containers", False),
                  ("file", "file", "Link file", "links.txt"),
                  ("interval", "int", "File / folder check interval in seconds (minimum 20)", 60),
                  ("enable_extension_filter", "bool", "Extension filter", False),
                  ("extension_filter", "str", "Extensions to look for (comma separated)", "dlc"),
                  ("add_to", "Collector;Queue", "Add files to", "Queue")]

    __description__ = """Observe folder and file for changes and add container and links"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def activate(self):
        self.extensions = None
        if self.config.get("enable_extension_filter"):
            extension_filter = self.config.get("extension_filter")
            self.extensions = [s.strip() for s in extension_filter.split(",")]
            self.log_info(_("Watching only for extensions [%s]") %
                          ",".join(["'%s'" % ext for ext in self.extensions]))

        interval = max(self.config.get('interval'), 20)
        self.periodical.start(interval, threaded=True)

    def periodical_task(self):
        folder = fs_encode(self.config.get('folder'))
        file = fs_encode(self.config.get('file'))
        add_to = 0 if self.config.get("add_to") == "Collector" else 1

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

                    name = "%s_%s.txt" % (file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(fsjoin(folder, "finished", name), "wb") as f:
                        f.write(content)

                    self.pyload.api.addPackage(f.name, [f.name], add_to)

            for f in os.listdir(folder):
                path = os.path.join(folder, f)

                if not os.path.isfile(path) or f.endswith("~") or f.startswith("#") or f.startswith("."):
                    continue

                if self.extensions is not None:
                    extension = os.path.splitext(f)[1]
                    # Note that extension contains the leading dot
                    if len(extension) == 0 or extension[1:] not in self.extensions:
                        continue

                newpath = os.path.join(folder, "finished", "tmp_" + f if self.config.get('delete') else f)
                shutil.move(path, newpath)

                self.log_info(_("Added %s from HotFolder") % f)
                self.pyload.api.addPackage(f, [newpath], add_to)

        except (IOError, OSError), e:
            self.log_error(e, trace=True)
