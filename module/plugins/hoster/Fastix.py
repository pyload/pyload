# -*- coding: utf-8 -*-

import re
from urllib import unquote
from random import randrange
from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads
from module.utils import parseFileSize


class Fastix(Hoster):
    __name__ = "Fastix"
    __version__ = "0.02"
    __type__ = "hoster"

    __pattern__ = r"http?://.*fastix.ru\..*"
    __description__ = """Fastix hoster plugin"""
    __author_name__ = ("Massimo, Rosamilia")
    __author_mail__ = ("max@spiritix.eu")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."): #incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def init(self):
        self.tries = 0
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError("Please enter your Fastix account or deactivate this plugin")
            self.fail("No Fastix account provided")

        self.log.debug("Fastix: Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            in_file = open("fastix_api.txt","r")
            api_key = in_file.read()
            in_file.close()
            url = "http://fastix.ru/api_v2/?apikey=%s&sub=getdirectlink&link=%s" % (api_key,pyfile.url)
            page = self.load(url)
            data = json_loads(page)
            self.logDebug("Json data: %s" % str(data))
            if "error\":true" in page:
                self.offline()
            else:
                new_url = data["downloadlink"]

        self.logDebug("Fastix: New URL: %s" % new_url)

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
