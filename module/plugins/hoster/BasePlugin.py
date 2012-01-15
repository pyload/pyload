#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urlparse import urlparse

from module.network.HTTPRequest import BadHeader
from module.plugins.Hoster import Hoster
from module.utils import html_unescape

class BasePlugin(Hoster):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __pattern__ = r"^unmatchable$"
    __version__ = "0.14"
    __description__ = """Base Plugin when any other didnt fit"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        """main function"""

        #debug part, for api exerciser
        if pyfile.url.startswith("DEBUG_API"):
            self.multiDL = False
            return

#        self.__name__ = "NetloadIn"
#        pyfile.name = "test"
#        self.html = self.load("http://localhost:9000/short")
#        self.download("http://localhost:9000/short")
#        self.api = self.load("http://localhost:9000/short")
#        self.decryptCaptcha("http://localhost:9000/captcha")
#
#        if pyfile.url == "79":
#            self.core.api.addPackage("test", [str(i) for i in range(80)], 1)
#
#        return
        if pyfile.url.startswith("http"):

            try:
                self.downloadFile(pyfile)
            except BadHeader, e:
                if e.code in (401, 403):
                    self.logDebug("Auth required")

                    pwd = pyfile.package().password.strip()
                    if ":" not in pwd:
                        self.fail(_("Authorization required (username:password)"))

                    self.req.addAuth(pwd)
                    self.downloadFile(pyfile)
                else:
                    raise

        else:
            self.fail("No Plugin matched and not a downloadable url.")


    def downloadFile(self, pyfile):
        pyfile.name = html_unescape(urlparse(pyfile.url).path.split("/")[-1])
        self.download(pyfile.url, disposition=True)
