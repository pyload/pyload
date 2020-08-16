# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class UlozToFolder(BaseDecrypter):
    __name__ = "UlozToFolder"
    __type__ = "decrypter"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl)/(m|soubory)/.+"
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

    __description__ = """Uloz.to folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    FOLDER_PATTERN = r'<ul class="profile_files">(.*?)</ul>'
    LINK_PATTERN = r'<br /><a href="/(.+?)">.+?</a>'
    NEXT_PAGE_PATTERN = r'<a class="next " href="/(.+?)">&nbsp;</a>'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []
        for i in range(1, 100):
            self.log_info(self._("Fetching links from page {}").format(i))
            m = re.search(self.FOLDER_PATTERN, html, re.S)
            if m is None:
                self.error(self._("FOLDER_PATTERN not found"))

            new_links.extend(re.findall(self.LINK_PATTERN, m.group(1)))
            m = re.search(self.NEXT_PAGE_PATTERN, html)
            if m is not None:
                html = self.load("http://ulozto.net/" + m.group(1))
            else:
                break
        else:
            self.log_info(self._("Limit of 99 pages reached, aborting"))

        if new_links:
            self.links = [["http://ulozto.net/{}".format(s) for s in new_links]]
