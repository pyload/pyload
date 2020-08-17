# -*- coding: utf-8 -*-
import re

from ..base.decrypter import BaseDecrypter


class QuickshareCzFolder(BaseDecrypter):
    __name__ = "QuickshareCzFolder"
    __type__ = "decrypter"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?quickshare\.cz/slozka-\d+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Quickshare.cz folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    FOLDER_PATTERN = r"<textarea.*?>(.*?)</textarea>"
    LINK_PATTERN = r"(http://www\.quickshare\.cz/\S+)"

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.S)
        if m is None:
            self.error(self._("FOLDER_PATTERN not found"))
        self.links.extend(re.findall(self.LINK_PATTERN, m.group(1)))
