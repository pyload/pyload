#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import tempfile
import urllib2

from module.plugins.Plugin import Plugin
from module.network.MultipartPostHandler import MultipartPostHandler

class CCF(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "CCF"
        props['type'] = "container"
        props['pattern'] = r"(?!http://).*\.ccf"
        props['version'] = "0.1"
        props['description'] = """CCF Container Convert Plugin"""
        props['author_name'] = ("Willnix")
        props['author_mail'] = ("Willnix@pyload.org")
        self.props = props
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

