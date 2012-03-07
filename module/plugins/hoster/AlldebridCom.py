#!/usr/nv python
# -*- coding: utf-8 -*-

import BeautifulSoup
from urllib import quote, unquote
from random import randrange

from module.plugins.Hoster import Hoster

class AlldebridCom(Hoster):
    __name__ = "AlldebridCom"
    __version__ = "0.1"
    __type__ = "hoster"

    __pattern__ = r"https?://.*alldebrid\..*"
    __description__ = """Alldebrid.com hoster plugin"""
    __author_name__ = ("Andy, Voigt")
    __author_mail__ = ("spamsales@online.de")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."): #incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100,999)
        return name

    def init(self):
        self.tries = 0
        self.chunkLimit = 3
        self.resumeDownload = True


    def process(self, pyfile):                            
        url="http://www.alldebrid.com/service.php?link=%s" %(pyfile.url)
        
        page = self.load(url)

        soup = BeautifulSoup.BeautifulSoup(page)
        for link in soup.findAll("a"):
			new_url = link.get("href")


        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        self.log.debug("AllDebrid: New URL: %s" % new_url)


        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload(
                {"error": "<title>An error occured while processing your request</title>"})

        if check == "error":
            #usual this download can safely be retried
            self.retry(reason="An error occured while generating link.", wait_time=60)

