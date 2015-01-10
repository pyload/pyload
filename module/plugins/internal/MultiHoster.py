# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.32"

    __pattern__ = r'^unmatchable$'

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    CHECK_TRAFFIC = True
    LOGIN_ACCOUNT = True


    def setup(self):
        self.chunkLimit     = 1
        self.multiDL        = bool(self.account)
        self.resumeDownload = self.premium


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

        if self.__pattern__ != r'^unmatchable$' and re.match(self.__pattern__, pyfile.url):
            self.checkInfo()

        if self.directDL:
            self.logDebug("Looking for direct download link...")
            self.handleDirect(pyfile)

        if not self.link and not self.lastDownload:
            self.preload()

            self.checkErrors()
            self.checkStatus(getinfo=False)

            if self.premium and (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium(pyfile)

            elif not self.LOGIN_ACCOUNT or (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as free download")
                self.handleFree(pyfile)

        self.downloadLink(self.link)
        self.checkFile()


    #@TODO: Remove in 0.4.10
    def downloadLink(self, link):
        if link and isinstance(link, basestring):
            self.correctCaptcha()
            self.download(link, disposition=True)


    def handlePremium(self, pyfile):
        return self.handleFree(pyfile)


    def handleFree(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
