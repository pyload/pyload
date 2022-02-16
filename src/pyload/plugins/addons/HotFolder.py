# -*- coding: utf-8 -*-
import os
import shutil
import time

from ..base.addon import BaseAddon


class HotFolder(BaseAddon):
    __name__ = "HotFolder"
    __type__ = "addon"
    __version__ = "0.26"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("folder", "folder", "Folder to watch", "watchdir"),
        ("watchfile", "bool", "Watch link file", False),
        ("delete", "bool", "Delete added containers", False),
        ("file", "str", "Link file", "links.txt"),
        ("interval", "int", "File / folder check interval in seconds (minimum 20)", 60)
    ]

    __description__ = (
        """Observe folder and file for changes and add container and links"""
    )
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def activate(self):
        interval = max(self.config.get('interval'), 20)
        self.periodical.start(interval, threaded=True)

    def periodical_task(self):
        watch_folder = os.fsdecode(self.config.get("folder"))
        watch_file = os.fsdecode(self.config.get("file"))

        try:
            if not os.path.isdir(os.path.join(watch_folder, "finished")):
                os.makedirs(os.path.join(watch_folder, "finished"), exist_ok=True)

            if self.config.get("watchfile"):
                with open(watch_file, mode="a+") as fp:
                    fp.seek(0)
                    content = fp.read().strip()

                if content:
                    fp = open(watch_file, mode="w")
                    fp.close()

                    name = "{}_{}.txt".format(watch_file, time.strftime("%H-%M-%S_%d%b%Y"))

                    with open(os.path.join(watch_folder, "finished", name), mode="w") as fp:
                        fp.write(content)

                    self.pyload.api.add_package(name, [fp.name], 1)

            for entry in os.listdir(watch_folder):
                entry_file = os.path.join(watch_folder, entry)

                if (
                    not os.path.isfile(entry_file)
                    or entry.endswith("~")
                    or entry.startswith("#")
                    or entry.startswith(".")
                    or os.path.realpath(watch_file) == os.path.realpath(entry_file)
                ):
                    continue

                new_path = os.path.join(
                    watch_folder,
                    "finished",
                    "tmp_" + entry if self.config.get("delete") else entry,
                )
                shutil.move(entry_file, new_path)

                self.log_info(self._("Added {} from HotFolder").format(entry))
                self.pyload.api.add_package(entry, [new_path], 1)

        except (IOError, OSError) as exc:
            self.log_error(
                exc, exc_info=self.pyload.debug > 1, stack_info=self.pyload.debug > 2
            )
