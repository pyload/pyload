# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class MBLinkInfo(Crypter):
    __name__ = "MBLinkInfo"
    __type__ = "container"
    __pattern__ = r"http://(?:www\.)?mblink\.info/?\?id=(\d+)"
    __version__ = "0.02"
    __description__ = """MBLink.Info Container Plugin"""
    __author_name__ = ("Gummibaer", "stickell")
    __author_mail__ = ("Gummibaer@wiki-bierkiste.de", "l.stickell@yahoo.it")

    URL_PATTERN = r'<meta[^;]+; URL=(.*)["\']>'

    def decrypt(self, pyfile):
        src = self.load(pyfile.url)
        found = re.search(self.URL_PATTERN, src)
        if found:
            link = found.group(1)
            self.logDebug("Redirected to " + link)
            self.core.files.addLinks([link], self.pyfile.package().id)
        else:
            self.fail('Unable to detect valid link')
