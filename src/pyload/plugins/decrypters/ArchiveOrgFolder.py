# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class ArchiveOrgFolder(BaseDecrypter):
    __name__ = "ArchiveOrgFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?archive\.org/details/.+"
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

    __description__ = """Archive.org decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LINK_PATTERN = r'<div><a href="(https://archive\.org/download/.+?)"'

    NAME_PATTERN = r'itemprop="name">(.+?)<'

    OFFLINE_PATTERN = r"Item cannot be found."
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        m = re.search(self.NAME_PATTERN, self.data)
        if m is not None:
            name = m.group(1)
        else:
            name = pyfile.package().name

        links = re.findall(self.LINK_PATTERN, self.data)
        self.packages = [(name, links, name)]
