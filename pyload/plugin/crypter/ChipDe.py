# -*- coding: utf-8 -*-

import re
from pyload.plugin.Crypter import Crypter


class ChipDe(Crypter):
    __name    = "ChipDe"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?chip\.de/video/.+\.html'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Chip.de decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("4Christopher", "4Christopher@gmx.de")]


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        try:
            f = re.search(r'"(http://video\.chip\.de/.+)"', self.html)
        except Exception:
            self.fail(_("Failed to find the URL"))
        else:
            self.urls = [f.group(1)]
            self.logDebug("The file URL is %s" % self.urls[0])
