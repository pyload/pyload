# -*- coding: utf-8 -*-

import re

from module.plugins.Plugin import Fail, Retry
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns, set_cookies


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.39"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LOGIN_ACCOUNT = True


    def setup(self):
        self.chunkLimit     = 1
        self.multiDL        = bool(self.account)
        self.resumeDownload = self.premium


    def prepare(self):
        self.info     = {}
        self.html     = ""
        self.link     = ""     #@TODO: Move to hoster class in 0.4.10
        self.directDL = False  #@TODO: Move to hoster class in 0.4.10

        if not self.getConfig('use_premium', True):
            self.retryFree()

        if self.LOGIN_ACCOUNT and not self.account:
            self.fail(_("Required account not found"))

        self.req.setOption("timeout", 120)

        if isinstance(self.COOKIES, list):
            set_cookies(self.req.cj, self.COOKIES)

        if self.DIRECT_LINK is None:
            self.directDL = self.__pattern__ != r'^unmatchable$' and re.match(self.__pattern__, self.pyfile.url)
        else:
            self.directDL = self.DIRECT_LINK

        self.pyfile.url = replace_patterns(self.pyfile.url, self.URL_REPLACEMENTS)


    def process(self, pyfile):
        try:
            self.prepare()

            if self.directDL:
                self.checkInfo()
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

            self.downloadLink(self.link, True)
            self.checkFile()

        except Fail, e:  #@TODO: Move to PluginThread in 0.4.10
            if self.premium:
                self.logWarning(_("Premium download failed"))
                self.retryFree()

            elif self.getConfig("revertfailed", True) \
                 and "new_module" in self.core.pluginManager.hosterPlugins[self.__name__]:
                hdict = self.core.pluginManager.hosterPlugins[self.__name__]

                tmp_module = hdict['new_module']
                tmp_name   = hdict['new_name']
                hdict.pop('new_module', None)
                hdict.pop('new_name', None)

                pyfile.initPlugin()

                hdict['new_module'] = tmp_module
                hdict['new_name']   = tmp_name

                raise Retry(_("Revert to original hoster plugin"))

            else:
                raise Fail(e)


    def handlePremium(self, pyfile):
        return self.handleFree(pyfile)


    def handleFree(self, pyfile):
        if self.premium:
            raise NotImplementedError
        else:
            self.fail(_("Required premium account not found"))
