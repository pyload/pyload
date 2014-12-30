# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.27"

    __pattern__ = r'^unmatchable$'

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_ACCOUNT = True


    def setup(self):
        self.chunkLimit = 1
        self.multiDL    = self.premium


    def prepare(self):
        self.info      = {}
        self.link      = ""     #@TODO: Move to hoster class in 0.4.10
        self.directDL  = False  #@TODO: Move to hoster class in 0.4.10

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.DIRECT_LINK is None:
            self.directDL = self.__pattern__ != r'^unmatchable$'
        else:
            self.directDL = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url,
                                           self.FILE_URL_REPLACEMENTS if hasattr(self, "FILE_URL_REPLACEMENTS") else self.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10


    def process(self, pyfile):
        self.prepare()

        if self.directDL:
            self.logDebug("Looking for direct download link...")
            self.handleDirect()

        if self.link:
            self.pyfile.url = self.link
            self.checkNameSize()

        elif not self.lastDownload:
            self.preload()
            self.checkInfo()

            if self.premium and (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium()
            else:
                self.logDebug("Handled as free download")
                self.handleFree()

        self.downloadLink(self.link)
        self.checkFile()


    def handlePremium(self, pyfile=None):
        return self.handleFree(pyfile)


    def handleFree(self, pyfile=None):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
