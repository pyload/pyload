# -*- coding: utf-8 -*-

import re
from pyload.plugin.Crypter import Crypter


class CzshareCom(Crypter):
    __name    = "CzshareCom"
    __type    = "crypter"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?(czshare|sdilej)\.(com|cz)/folders/.+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Czshare.com folder decrypter plugin, now Sdilej.cz"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_PATTERN = r'<tr class="subdirectory">\s*<td>\s*<table>(.*?)</table>'
    LINK_PATTERN = r'<td class="col2"><a href="([^"]+)">info</a></td>'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.S)
        if m is None:
            self.error(_("FOLDER_PATTERN not found"))

        self.urls.extend(re.findall(self.LINK_PATTERN, m.group(1)))
