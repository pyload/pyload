# -*- coding: utf-8 -*-

import re
from urllib import unquote
from random import randrange
from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads
from module.utils import parseFileSize


class AlldebridCom(Hoster):
    __name__ = "AlldebridCom"
    __version__ = "0.34"
    __type__ = "hoster"
    __pattern__ = r"https?://.*alldebrid\..*"
    __description__ = """Alldebrid.com hoster plugin"""
    __author_name__ = ("Andy, Voigt", "Walter Purcaro")
    __author_mail__ = ("spamsales@online.de", "vuolter@gmail.com")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."

        if name.endswith("..."): #incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)

        return name

    def setup(self):
        self.chunkLimit = 16
        self.resumeDownload = True

    def process(self, pyfile):
        url_old = pyfile.url

        if re.match(self.__pattern__, pyfile.url):
            url_new = pyfile.url
        elif not self.account:
            self.fail("No account provided")
        else:
            password = self.getPassword().splitlines()
            password = "" if not password else password[0]

            url = "http://www.alldebrid.com/service.php?link=%s&json=true&pw=%s" % (pyfile.url, password)
            page = self.load(url)
            data = json_loads(page)

            self.logDebug("Json data: %s" % str(data))

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
                url_new = data["link"]

        url_new = url_new.replace("http://", "https://") if self.getConfig("https") else \
                  url_new.replace("https://", "http://")

        if url_new != url_old:
            self.logDebug("Old URL: %s" % url_old)
            self.logDebug("New URL: %s" % url_new)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(url_new)

        self.download(url_new, disposition=True)

        check = self.checkDownload({"error": "<title>An error occured while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(reason="An error occured while generating link.", wait_time=60)
        elif check == "empty":
            self.retry(reason="Downloaded File was empty.", wait_time=60)
