# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter

import re


class TnyCz(SimpleCrypter):
    __name__ = "TnyCz"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?tny\.cz/\w+'

    __description__ = """Tny.cz decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    TITLE_PATTERN = r'<title>(?P<title>.+) - .+</title>'


    def getLinks(self):
        m = re.search(r'<a id=\'save_paste\' href="(.+save\.php\?hash=.+)">', self.html)
        return re.findall(".+", self.load(m.group(1), decode=True)) if m else None
