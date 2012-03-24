#!/usr/nv python
# -*- coding: utf-8 -*-

import re
from urllib import quote, unquote
from random import randrange
from os import stat

from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads
from module.utils import parseFileSize, fs_encode


class AlldebridCom(Hoster):
    __name__ = "AlldebridCom"
    __version__ = "0.2"
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
        if not self.account:
            self.logError(_("Please enter your AllDebrid account or deactivate this plugin"))
            self.fail("No AllDebrid account provided")

        self.log.debug("AllDebrid: Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            password = self.getPassword().splitlines()
            if not password: password = ""
            else: password = password[0]

            url = "http://www.alldebrid.com/service.php?link=%s&json=true&pw=%s" %(pyfile.url, password)
            page = self.load(url)
            data = json_loads(page)
            
            self.log.debug("Json data: %s" % str(data))

            if data["error"]:
                if data["error"] == "This link isn't available on the hoster website.":
                   self.offline()
                else:
                    self.logWarning(data["error"])
                    self.tempOffline()
            else:
                if self.pyfile.name and not self.pyfile.name.endswith('.tmp'):
                    self.pyfile.name = data["filename"]
                self.pyfile.size = parseFileSize(data["filesize"])
                new_url = data["link"]

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
                {"error": "<title>An error occured while processing your request</title>","empty": re.compile(r"^$")})

        if check == "error":
            self.retry(reason="An error occured while generating link.", wait_time=60)
        else:
            if check == "empty":
                self.retry(reason="Downloaded File was empty.", wait_time=60)

