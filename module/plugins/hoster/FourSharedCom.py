#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster
from module.network.RequestFactory import getURL
import re

def getInfo(urls):
    result = []

    for url in urls:
        name, size, status, url = parseFileInfo(FourSharedCom, url, getURL(url, decode=True)) 
        if status == 2:
            name = re.sub(r"&#(\d+).", lambda m: unichr(int(m.group(1))), name)    
        result.append(name, size, status, url)
            
    yield result

class FourSharedCom(SimpleHoster):
    __name__ = "FourSharedCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?4shared(-china)?\.com/(account/)?(download|get|file|document|photo|video|audio)/.+?/.*"
    __version__ = "0.21"
    __description__ = """4Shared Download Hoster"""
    __author_name__ = ("jeix", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = '<meta name="title" content="([^"]+)" />'
    FILE_SIZE_PATTERN = '<span title="Size: ([0-9,.]+) ([kKMG]i?B)">'
    FILE_OFFLINE_PATTERN = 'The file link that you requested is not valid\.|This file was deleted.'
    FREE_LINK_PATTERN = '<a href="([^"]+)"   class="dbtn"'
    DOWNLOAD_URL_PATTERN = "<div class=\"(?:dl|xxlarge bold)\">\s*<a href='([^']+)'"

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()
        pyfile.name = re.sub(r"&#(\d+).", lambda m: unichr(int(m.group(1))), pyfile.name)
        self.handleFree()

    def handleFree(self):
        found = re.search(self.FREE_LINK_PATTERN, self.html)
        if not found: raise PluginParseError('Free download button')
        link = found.group(1)
        
        self.html = self.load(link)
                
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: raise PluginParseError('Download link')
        link = found.group(1)
        
        self.setWait(20)
        self.wait()
        self.download(link)

            