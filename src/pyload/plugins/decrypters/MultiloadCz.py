# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class MultiloadCz(BaseDecrypter):
    __name__ = "MultiloadCz"
    __type__ = "decrypter"
    __version__ = "0.46"
    __status__ = "testing"

    __pattern__ = r"http://(?:[^/]*\.)?multiload\.cz/(stahnout|slozka)/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("use_subfolder", "bool", "Save package to subfolder", True),
        ("subfolder_per_package", "bool", "Create a subfolder for each package", True),
        ("usedHoster", "str", "Prefered hoster list (bar-separated)", ""),
        ("ignoredHoster", "str", "Ignored hoster list (bar-separated)", ""),
    ]

    __description__ = """Multiload.cz decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    FOLDER_PATTERN = (
        r'<form action="" method="get"><textarea.*?>([^>]*)</textarea></form>'
    )
    LINK_PATTERN = r'<p class="manager-server"><strong>(.+?)</strong></p><p class="manager-linky"><a href="(.+?)">'

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        if re.match(self.__pattern__, pyfile.url).group(1) == "slozka":
            m = re.search(self.FOLDER_PATTERN, self.data)
            if m is not None:
                self.links.extend(m.group(1).split())
        else:
            m = re.findall(self.LINK_PATTERN, self.data)
            if m is not None:
                prefered_set = set(self.config.get("usedHoster").split("|"))
                self.links.extend(x[1] for x in m if x[0] in prefered_set)

                if not self.links:
                    ignored_set = set(self.config.get("ignoredHoster").split("|"))
                    self.links.extend(x[1] for x in m if x[0] not in ignored_set)
