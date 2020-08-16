# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class DatafileComFolder(BaseDecrypter):
    __name__ = "DatafileComFolder"
    __type__ = "decrypter"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?datafile\.com/f/\w{12}"
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
    ]

    __description__ = """datafile.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LINK_PATTERN = r"https?://(?:www\.)?datafile\.com/d/\w{17}"
    NAME_PATTERN = r'<div class="file-name">(?P<N>.+?)<'

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        links = re.findall(self.LINK_PATTERN, self.data)

        m = re.search(self.NAME_PATTERN, self.data)
        if m is not None:
            name = m.group("N")
            self.packages.append((name, links, name))

        else:
            self.links.extend(links)
