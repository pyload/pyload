#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import sleep

from module.plugins.Crypter import Crypter

class DDLMusicOrg(Crypter):
    __name__ = "DDLMusicOrg"
    __type__ = "container"
    __pattern__ = r"http://[\w\.]*?ddl-music\.org/captcha/ddlm_cr\d\.php\?\d+\?\d+"
    __version__ = "0.1"
    __description__ = """ddl-music.org Container Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url, cookies=True)

    def file_exists(self):
        """ returns True or False
        """
        if not self.html:
            self.download_html()
        if re.search(r"Wer dies nicht rechnen kann", self.html) != None:
            return True
        return False

    def proceed(self, url, location):
        for i in range(5):
            self.download_html()
            posturl = re.search(r"id=\"captcha\" action=\"(/captcha/ddlm_cr\d\.php)\"", self.html).group(1)
            math = re.search(r"(\d+) ([\+-]) (\d+) =\s+<inp", self.html)
            id = re.search(r"name=\"id\" value=\"(\d+)\"", self.html).group(1)
            linknr = re.search(r"name=\"linknr\" value=\"(\d+)\"", self.html).group(1)
            
            solve = ""
            if math.group(2) == "+":
                solve = int(math.group(1)) + int(math.group(3))
            else:
                solve = int(math.group(1)) - int(math.group(3))
            sleep(3)
            htmlwithlink = self.req.load("http://ddl-music.org%s" % posturl, cookies=True, post={"calc%s" % linknr:solve, "send%s" % linknr:"Send", "id":id, "linknr":linknr})
            m = re.search(r"<form id=\"ff\" action=\"(.*?)\" method=\"post\">", htmlwithlink)
            if m:
                self.links = [m.group(1)]
                return
        self.links = False
