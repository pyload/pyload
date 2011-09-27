#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class ShareRapidCom(Hoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?(share-rapid)?(.com|.cz)/"
    __version__ = "0.1"
    __description__ = """share-rapid Plugin"""
    __author_name__ = ("MikyWoW")
    __author_mail__ = ("MikyWoW@seznam.cz")

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        name = pyfile.url
        if "?" in pyfile.url:
           name = re.findall("([^?=]+)", name)[-3]
        
        pyfile.name = re.findall("([^/=]+)", name)[-1]

        self.html = self.load(pyfile.url)

        if "Stahování je pøístupné pouze pøihlášeným uživatelùm" in self.html:
           self.fail("Nepøihlášen")
        else:
             start = self.html.index('<a href="http://s')
             self.html = self.html[start+9:]
             start = self.html.index('"')
             self.html = self.html[0:start]
             self.download(self.html)