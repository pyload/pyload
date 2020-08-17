# -*- coding: utf-8 -*-
import re
import urllib.parse

from ..base.decrypter import BaseDecrypter


class HearthisAtFolder(BaseDecrypter):
    __name__ = "HearthisAtFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?hearthis\.at/.*(?<!#pyload)$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("dl_subfolders", "bool", "Download subfolders", False),
        ("package_subfolder", "bool", "Subfolder as a separate package", False),
    ]

    __description__ = """Hearthis.at folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        m = re.search(r"intTrackId = (\d+);", self.data)
        if m is not None:
            #: Single track
            self.packages = [
                (pyfile.package().name, pyfile.url + "#pyload", pyfile.package().folder)
            ]

        else:
            #: Playlist
            m = re.search(r"intInternalId = (\d+);", self.data)
            if m is None:
                self.fail(self._("Internal Id not found"))

            self.data = self.load(
                "https://hearthis.at/user_ajax_more.php",
                post={"user": m.group(1), "min": 0, "max": 200},
            )

            links = [
                urllib.parse.urljoin(pyfile.url, x) + "#pyload"
                for x in re.findall(
                    r'<a class="player-link".+?href="(.+?)".+?</a>', self.data, re.S
                )
            ]
            self.packages = [(pyfile.package().name, links, pyfile.package().folder)]
