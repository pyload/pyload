#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import tempfile
import urllib2

from module.plugins.Container import Container
from module.network.MultipartPostHandler import MultipartPostHandler

class CCF(Container):
    __name__ = "CCF"
    __version__ = "0.1"
    __pattern__ = r"(?!http://).*\.ccf"
    __description__ = """CCF Container Convert Plugin"""
    __author_name__ = ("Willnix")
    __author_mail__ = ("Willnix@pyload.org")

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.parent = parent
        self.multi_dl = True
        self.links = []

    def proceed(self, url, location):
        infile = url.replace("\n", "")

        opener = urllib2.build_opener(MultipartPostHandler)
        params = {"src": "ccf",
            "filename": "test.ccf",
            "upload": open(infile, "rb")}
        tempdlc_content = opener.open('http://service.jdownloader.net/dlcrypt/getDLC.php', params).read()

        tempdlc = tempfile.NamedTemporaryFile(delete=False, suffix='.dlc')
        tempdlc.write(re.search(r'<dlc>(.*)</dlc>', tempdlc_content, re.DOTALL).group(1))
        tempdlc.close()

        self.links.append(tempdlc.name)

        return True

