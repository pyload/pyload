# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.Hoster import Hoster
from module.utils import parseFileSize


class AlldebridCom(Hoster):
    __name__ = "AlldebridCom"
    __type__ = "hoster"
    __version__ = "0.34"

    __pattern__ = r'https?://(?:[^/]*\.)?alldebrid\..*'

    __description__ = """Alldebrid.com hoster plugin"""
    __author_name__ = "Andy Voigt"
    __author_mail__ = "spamsales@online.de"


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def setup(self):
        self.chunkLimit = 16
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "AllDebrid")
            self.fail("No AllDebrid account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            password = self.getPassword().splitlines()
            password = "" if not password else password[0]

            url = "http://www.alldebrid.com/service.php?link=%s&json=true&pw=%s" % (pyfile.url, password)
            page = self.load(url)
            data = json_loads(page)

            self.logDebug("Json data: %s" % str(data))

            if data['error']:
                if data['error'] == "This link isn't available on the hoster website.":
                    self.offline()
                else:
                    self.logWarning(data['error'])
                    self.tempOffline()
            else:
                if pyfile.name and not pyfile.name.endswith('.tmp'):
                    pyfile.name = data['filename']
                pyfile.size = parseFileSize(data['filesize'])
                new_url = data['link']

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"error": "<title>An error occured while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(wait_time=60, reason="An error occured while generating link.")
        elif check == "empty":
            self.retry(wait_time=60, reason="Downloaded File was empty.")
