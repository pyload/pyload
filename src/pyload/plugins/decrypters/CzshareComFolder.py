# -*- coding: utf-8 -*-
import re

from ..base.decrypter import BaseDecrypter


class CzshareComFolder(BaseDecrypter):
    __name__ = "CzshareComFolder"
    __type__ = "decrypter"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?(czshare|sdilej)\.(com|cz)/folders/.+"
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

    __description__ = """Czshare.com folder decrypter plugin, now Sdilej.cz"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    FOLDER_PATTERN = r'<tr class="subdirectory">\s*<td>\s*<table>(.*?)</table>'
    LINK_PATTERN = r'<td class="col2"><a href="(.+?)">info</a></td>'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.S)
        if m is None:
            self.error(self._("FOLDER_PATTERN not found"))

        self.links.extend(re.findall(self.LINK_PATTERN, m.group(1)))
