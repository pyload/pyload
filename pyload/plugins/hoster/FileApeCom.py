#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

class FileApeCom(Hoster):
    __name__ = "FileApeCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+"
    __version__ = "0.1"
    __description__ = """FileApe Download Hoster"""
    __author_name__ = ("espes")

    def setup(self):
        self.multiDL = False
        self.html = None

    def process(self, pyfile):
        self.pyfile = pyfile

        self.html = self.load(self.pyfile.url)
        
        if "This file is either temporarily unavailable or does not exist" in self.html:
            self.offline()
        
        self.html = self.load(self.pyfile.url+"&g=1")
        
        continueMatch = re.search(r"window\.location = '(http://.*?)'", self.html)
        if not continueMatch:
            continueMatch = re.search(r"'(http://fileape\.com/\?act=download&t=[A-Za-z0-9_-]+)'", self.html)
        if continueMatch:
            continuePage = continueMatch.group(1)
        else:
            self.fail("Plugin Defect") 
        
        wait = 60
        waitMatch = re.search("id=\"waitnumber\" style=\"font-size:2em; text-align:center; width:33px; height:33px;\">(\\d+)</span>", self.html)
        if waitMatch:
            wait = int(waitMatch.group(1))
        self.setWait(wait+3)
        self.wait()
        
        self.html = self.load(continuePage)
        linkMatch = \
            re.search(r"<div style=\"text-align:center; font-size: 30px;\"><a href=\"(http://.*?)\"", self.html)
        if not linkMatch:
            linkMatch = re.search(r"\"(http://tx\d+\.fileape\.com/[a-z]+/.*?)\"", self.html)
        if linkMatch:
            link = linkMatch.group(1)
        else:
            self.fail("Plugin Defect")
        
        pyfile.name = link.rpartition('/')[2]
        
        self.download(link)
        
        check = self.checkDownload({"exp": "Download ticket expired"})
        if check == "exp":
            self.log.info("Ticket expired, retrying...")
            self.retry()