# -*- coding: utf-8 -*-

import re
from pyload.plugin.Crypter import Crypter


class QuickshareCz(Crypter):
    __name    = "QuickshareCz"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?quickshare\.cz/slozka-\d+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Quickshare.cz folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_PATTERN = r'<textarea.*?>(.*?)</textarea>'
    LINK_PATTERN = r'(http://www\.quickshare\.cz/\S+)'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.S)
        if m is None:
            self.error(_("FOLDER_PATTERN not found"))
        self.urls.extend(re.findall(self.LINK_PATTERN, m.group(1)))
