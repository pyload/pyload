# -*- coding: utf-8 -*-

import pycurl

from ..base.decrypter import BaseDecrypter


class ShSt(BaseDecrypter):
    __name__ = "ShSt"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://sh\.st/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Sh.St decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Frederik Möllers", "fred-public@posteo.de")]

    NAME_PATTERN = r"<title>(?P<N>.+?) -"

    def decrypt(self, pyfile):
        #: If we use curl as a user agent, we will get a straight redirect (no waiting!)
        self.req.http.c.setopt(pycurl.USERAGENT, "curl/7.42.1")
        #: Fetch the target URL
        header = self.load(self.pyfile.url, just_header=True, decode=False)
        target_url = header.get("location")
        self.links.append(target_url)
