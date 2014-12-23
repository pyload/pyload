# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.23"

    __pattern__ = r'^unmatchable$'

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    DIRECT_LINK   = True
    MULTI_HOSTER  = True
    LOGIN_ACCOUNT = True
    LOGIN_PREMIUM = False


    def setup(self):
        self.chunkLimit = 1
        self.multiDL    = self.premium


    def prepare(self):
        self.info      = {}
        self.link      = ""
        self.multihost = False

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.DIRECT_LINK is None:
            self.directDL = bool(self.account)
        else:
            self.directDL = self.DIRECT_LINK

        if (self.__pattern__ != self.core.pluginManager.hosterPlugins[self.__name__]['pattern']
            or re.match(self.__pattern__, self.pyfile.url) is None):

            if self.LOGIN_ACCOUNT and not self.account:
                self.logError(_("Required account not found"))

            elif self.LOGIN_PREMIUM and not self.premium:
                self.logError(_("Required premium account not found"))

            else:
                self.multihost = True

        self.pyfile.url = replace_patterns(self.pyfile.url,
                                           self.FILE_URL_REPLACEMENTS if hasattr(self, "FILE_URL_REPLACEMENTS") else self.URL_REPLACEMENTS)  #@TODO: Remove FILE_URL_REPLACEMENTS check in 0.4.10


    def handleMulti(self):
        raise NotImplementedError
