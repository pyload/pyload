# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FreetexthostCom(SimpleCrypter):
    __name__    = "FreetexthostCom"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?freetexthost\.com/\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Freetexthost.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def get_links(self):
        m = re.search(r'<div id="contentsinner">\s*(.+)<div class="viewcount">', self.html, re.S)
        if m is None:
            self.error(_("Unable to extract links"))
        links = m.group(1)
        return links.strip().split("<br />\r\n")


getInfo = create_getInfo(FreetexthostCom)
