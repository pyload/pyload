# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.Hoster import Hoster


class FastixRu(Hoster):
    __name__ = "FastixRu"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?fastix\.(ru|it)/file/(?P<ID>[a-zA-Z0-9]{24})'

    __description__ = """Fastix hoster plugin"""
    __author_name__ = "Massimo Rosamilia"
    __author_mail__ = "max@spiritix.eu"


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name

    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Fastix")
            self.fail("No Fastix account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            api_key = self.account.getAccountData(self.user)
            api_key = api_key['api']
            url = "http://fastix.ru/api_v2/?apikey=%s&sub=getdirectlink&link=%s" % (api_key, pyfile.url)
            page = self.load(url)
            data = json_loads(page)
            self.logDebug("Json data: %s" % str(data))
            if "error\":true" in page:
                self.offline()
            else:
                new_url = data['downloadlink']

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"error": "<title>An error occurred while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(wait_time=60, reason="An error occurred while generating link.")
        elif check == "empty":
            self.retry(wait_time=60, reason="Downloaded File was empty.")
