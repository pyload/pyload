# -*- coding: utf-8 -*-

import re

from ..internal.Crypter import Crypter


class UlozToFolder(Crypter):
    __name__ = "UlozToFolder"
    __type__ = "crypter"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl)/(m|soubory)/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

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
            self.log_info(_("Fetching links from page %i") % i)
            m = re.search(self.FOLDER_PATTERN, html, re.S)
            if m is None:
                self.error(_("FOLDER_PATTERN not found"))

            new_links.extend(re.findall(self.LINK_PATTERN, m.group(1)))
            m = re.search(self.NEXT_PAGE_PATTERN, html)
            if m is not None:
                html = self.load("http://ulozto.net/" + m.group(1))
            else:
                break
        else:
            self.log_info(_("Limit of 99 pages reached, aborting"))

        if new_links:
            self.links = [map(lambda s: "http://ulozto.net/%s" % s, new_links)]
