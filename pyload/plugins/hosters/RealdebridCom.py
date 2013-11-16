#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from urllib import quote, unquote
from random import randrange

from pyload.utils import parseFileSize
from pyload.utils import json_loads
from pyload.plugins.Hoster import Hoster


class RealdebridCom(Hoster):
    __name__ = "RealdebridCom"
    __version__ = "0.51"
    __type__ = "hoster"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("https", "bool", "Enable HTTPS", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]
    __pattern__ = r"https?://.*real-debrid\..*"
    __description__ = """Real-Debrid.com hoster plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if not name or name.endswith(".."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def init(self):
        self.tries = 0
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Real-debrid")
            self.fail("No Real-debrid account provided")

        self.logDebug("Real-Debrid: Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            password = self.getPassword().splitlines()
            if not password:
                password = ""
            else:
                password = password[0]

            url = "http://real-debrid.com/ajax/unrestrict.php?lang=en&link=%s&password=%s&time=%s" % (
                quote(pyfile.url, ""), password, int(time() * 1000))
            page = self.load(url)
            data = json_loads(page)

            self.logDebug("Returned Data: %s" % data)

            if data["error"] != 0:
                if data["message"] == "Your file is unavailable on the hoster.":
                    self.offline()
                else:
                    self.logWarning(data["message"])
                    self.tempOffline()
            else:
                if self.pyfile.name is not None and self.pyfile.name.endswith('.tmp') and data["file_name"]:
                    self.pyfile.name = data["file_name"]
                self.pyfile.size = parseFileSize(data["file_size"])
                new_url = data['generated_links'][0][-1]

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        self.logDebug("Real-Debrid: New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown") or pyfile.name.endswith('..'):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload(
            {"error": "<title>An error occured while processing your request</title>"})

        if check == "error":
            #usual this download can safely be retried
            self.retry(reason="An error occured while generating link.", wait_time=60)
