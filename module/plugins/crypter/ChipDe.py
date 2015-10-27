# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter, create_getInfo


class ChipDe(Crypter):
    __name__    = "ChipDe"
    __type__    = "crypter"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?chip\.de/video/.+\.html'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_premium"          , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Chip.de decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("4Christopher", "4Christopher@gmx.de")]


    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)
        try:
            f = re.search(r'"(http://video\.chip\.de/.+)"', self.data)

        except Exception:
            self.fail(_("Failed to find the URL"))

        else:
            self.links = [f.group(1)]
            self.log_debug("The file URL is %s" % self.links[0])


getInfo = create_getInfo(ChipDe)
