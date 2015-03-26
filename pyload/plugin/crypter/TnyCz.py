# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter

import re


class TnyCz(SimpleCrypter):
    __name__    = "TnyCz"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?tny\.cz/\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Tny.cz decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<title>(?P<N>.+) - .+</title>'


    def getLinks(self):
        m = re.search(r'<a id=\'save_paste\' href="(.+save\.php\?hash=.+)">', self.html)
        return re.findall(".+", self.load(m.group(1), decode=True)) if m else None
