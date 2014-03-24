# -*- coding: utf-8 -*-

import re
from urllib import quote, unquote
from random import randrange

from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads
from module.utils import parseFileSize

class OverLoadMe(Hoster):
    __name__ = "OverLoadMe"
    __version__ = "0.01"
    __type__ = "hoster"

    __pattern__ = r"https?://.*overload\.me.*"
    __description__ = """Over-Load.me hoster plugin"""
    __author_name__ = ("marley")
    __author_mail__ = ("marley@over-load.me")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def setup(self):
        self.chunkLimit = 5
        self.resumeDownload = True

    
    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Over-Load")
            self.fail("No Over-Load account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            data = self.account.getAccountData(self.user)
            
            page = self.load("https://api.over-load.me/getdownload.php" , get={"auth": data["password"], "link": pyfile.url})
            data = json_loads(page)
            
            self.logDebug("Returned Data: %s" % data)

            if data["err"] == 1:
                self.logWarning(data["msg"])
                self.tempOffline()
            else:
                if self.pyfile.name is not None and self.pyfile.name.endswith('.tmp') and data["filename"]:
                    self.pyfile.name = data["filename"]
                    self.pyfile.size =  parseFileSize(data["filesize"])
                new_url = data["downloadlink"]

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)
        
        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown") or pyfile.name.endswith('..'):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload(
            {"error": "<title>An error occured while processing your request</title>"})

        if check == "error":
            #usual this download can safely be retried
            self.retry(reason="An error occured while generating link.", wait_time=60)
