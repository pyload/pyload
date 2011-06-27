#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random

from module.utils import parseFileSize
from module.plugins.Hoster import Hoster

class ZShareNet(Hoster):
    __name__ = "ZShareNet"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?zshare\.net/(download|video|image|audio|flash)/.*"
    __version__ = "0.2"
    __description__ = """ZShareNet Download Hoster"""
    __author_name__ = ("espes","Cptn Sandwich")

    def setup(self):
        self.multiDL = False
        self.html = None

    def process(self, pyfile):
        self.pyfile = pyfile
        
        self.pyfile.url = re.sub("(video|image|audio|flash)","download",self.pyfile.url) 
        
        self.html = self.load(pyfile.url)
        if "File Not Found" in self.html:
            self.offline()
        
        filenameMatch = re.search("File Name:.*?<font color=\"#666666\".*?>(.*?)</font>", self.html, re.DOTALL)
        filesizeMatch = re.search("File Size:.*?<font color=\"#666666\".*?>([^<]+)</font>", self.html, re.DOTALL)
        if not filenameMatch or not filesizeMatch:
            self.offline()
        filename = filenameMatch.group(1)
        filesize = filesizeMatch.group(1)
        if filename.strip() == "":
            self.offline()
        
        pyfile.name = filename

        pyfile.size = parseFileSize(filesize)
      
        if '<input name="download"' not in self.html:
            self.fail("No download form")
        
        self.html = self.load(pyfile.url, post={
            "download": 1,
            "imageField.x": random.randrange(160),
            "imageField.y": random.randrange(60)})
        
        dllinkMatch = re.search("var link_enc\\=new Array\\(\\'(.*?)\\'\\)", self.html)
        if dllinkMatch:
            dllink = re.sub("\\'\\,\\'", "", dllinkMatch.group(1))
        else:
            self.fail("Plugin defect")
        
        self.setWait(51)
        self.wait()
        
        self.download(dllink)
        check = self.checkDownload({
            "unav": "/images/download.gif",
            "404": "404 - Not Found"
        })
        #print check
        if check == "unav":
            self.fail("Plugin defect")
        elif check == "404":
            self.offline()
