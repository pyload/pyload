# -*- coding: utf-8 -*-

import re
from urllib import unquote
from random import randrange
from pyload.plugins.Hoster import Hoster
from pyload.utils import json_loads


class FastixRu(Hoster):
    __name__ = "FastixRu"
    __version__ = "0.02"
    __type__ = "hoster"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]
    __pattern__ = r"http?://.*fastix.ru\..*"
    __description__ = """Fastix hoster plugin"""
    __author_name__ = ("Massimo, Rosamilia")
    __author_mail__ = ("max@spiritix.eu")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def init(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Fastix")
            self.fail("No Fastix account provided")

        self.logDebug("Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            api_key = self.account.getAccountData(self.user)
            api_key = api_key["api"]
            url = "http://fastix.ru/api_v2/?apikey=%s&sub=getdirectlink&link=%s" % (api_key, pyfile.url)
            page = self.load(url)
            data = json_loads(page)
            self.logDebug("Json data: %s" % str(data))
            if "error\":true" in page:
                self.offline()
            else:
                new_url = data["downloadlink"]

        self.logDebug("New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"error": "<title>An error occurred while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(reason="An error occurred while generating link.", wait_time=60)
        elif check == "empty":
            self.retry(reason="Downloaded File was empty.", wait_time=60)
