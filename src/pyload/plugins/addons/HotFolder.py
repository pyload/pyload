# -*- coding: utf-8 -*-
import os
import shutil
import time

from ..base.addon import Addon
from ..helpers import encode


class HotFolder(Addon):
    __name__ = "HotFolder"
    __type__ = "addon"
    __version__ = "0.24"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("folder", "str", "Folder to watch", "watchdir"),
        ("watchfile", "bool", "Watch link file", False),
        ("delete", "bool", "Delete added containers", False),
        ("file", "str", "Link file", "links.txt"),
    ]

    __description__ = (
        """Observe folder and file for changes and add container and links"""
    )
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.de")]

    def activate(self):
        self.periodical.start(60, threaded=True)

    def periodical_task(self):
        folder = encode(self.config.get("folder"))
        file = encode(self.config.get("file"))

        try:
            if not os.path.isdir(os.path.join(folder, "finished")):
                os.makedirs(os.path.join(folder, "finished"), exist_ok=True)

            if self.config.get("watchfile"):
                with open(file, mode="a+") as file:
                    file.seek(0)
                    content = file.read().strip()

                if content:
                    file = open(file, mode="w")
                    file.close()

                    name = "{}_{}.txt".format(file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(os.path.join(folder, "finished", name), mode="wb") as file:
                        file.write(content)

                    self.pyload.api.addPackage(file.name, [file.name], 1)

            for entry in os.listdir(folder):
                path = os.path.join(folder, entry)

                if (
                    not os.path.isfile(path)
                    or entry.endswith("~")
                    or entry.startswith("#")
                    or entry.startswith(".")
                ):
                    continue

                newpath = os.path.join(
                    folder, "finished", "tmp_" + entry if self.config.get("delete") else entry
                )
                shutil.move(path, newpath)

                self.log_info(self._("Added {} from HotFolder").format(entry))
                self.pyload.api.addPackage(entry, [newpath], 1)

        except (IOError, OSError) as exc:
            self.log_error(
                exc, exc_info=self.pyload.debug > 1, stack_info=self.pyload.debug > 2
            )
