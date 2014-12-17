# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastixRu(SimpleHoster):
    __name__    = "FastixRu"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?fastix\.(ru|it)/file/(?P<ID>\w{24})'

    __description__ = """Fastix hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    MULTI_HOSTER = True


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name


    def setup(self):
        self.chunkLimit     = 3
        self.resumeDownload = True


    def handleMulti(self):
        api_key = self.account.getAccountData(self.user)
        api_key = api_key['api']

        page = self.load("http://fastix.ru/api_v2/",
                         get={'apikey': api_key, 'sub': "getdirectlink", 'link': self.pyfile.url})
        data = json_loads(page)

        self.logDebug("Json data", data)

        if "error\":true" in page:
            self.offline()
        else:
            self.link = data['downloadlink']

        if self.link != self.pyfile.url:
            self.logDebug("New URL: %s" % self.link)

        if self.pyfile.name.startswith("http") or self.pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            self.pyfile.name = self.getFilename(self.link)


    def checkFile(self):
        check = self.checkDownload({"error": "<title>An error occurred while processing your request</title>",
                                    "empty": re.compile(r"^$")})

        if check == "error":
            self.retry(wait_time=60, reason=_("An error occurred while generating link"))
        elif check == "empty":
            self.retry(wait_time=60, reason=_("Downloaded File was empty"))


getInfo = create_getInfo(FastixRu)
