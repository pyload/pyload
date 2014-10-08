# -*- coding: utf-8 -*-

import re

from pycurl import FOLLOWLOCATION

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class File4safeCom(XFSPHoster):
    __name__ = "File4safeCom"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?file4safe\.com/\w{12}'

    __description__ = """File4safe.com hoster plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    HOSTER_NAME = "file4safe.com"


    def handlePremium(self):
        self.req.http.lastURL = self.pyfile.url

        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        self.load(self.pyfile.url, post=self.getPostParameters(), decode=True)
        self.header = self.req.http.header
        self.req.http.c.setopt(FOLLOWLOCATION, 1)

        m = re.search(r"Location\s*:\s*(.*)", self.header, re.I)
        if m and re.match(self.LINK_PATTERN, m.group(1)):
            location = m.group(1).strip()
            self.startDownload(location)
        else:
            self.parseError("Unable to detect premium download link")


getInfo = create_getInfo(File4safeCom)
