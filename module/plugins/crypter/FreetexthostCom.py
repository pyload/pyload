# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FreetexthostCom(SimpleCrypter):
    __name__ = "FreetexthostCom"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?freetexthost\.com/\w+'

    __description__ = """Freetexthost.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    def getLinks(self):
        m = re.search(r'<div id="contentsinner">\s*(.+)<div class="viewcount">', self.html, re.S)
        if m is None:
            self.fail('Unable to extract links | Plugin may be out-of-date')
        links = m.group(1)
        return links.strip().split("<br />\r\n")
