# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MultiHoster(SimpleHoster):
    __name__    = "MultiHoster"
    __type__    = "hoster"
    __version__ = "0.24"

    __pattern__ = r'^unmatchable$'

    __description__ = """Multi hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    DIRECT_LINK   = True


    def setup(self):
        self.chunkLimit = 1
        self.multiDL    = self.premium


    def process(self, pyfile):
        self.prepare()

        if self.directDL:
            self.logDebug("Looking for direct download link...")
            self.handleDirect()

        if not self.link and not self.lastDownload:
            self.preload()

            if self.premium and (not self.CHECK_TRAFFIC or self.checkTrafficLeft()):
                self.logDebug("Handled as premium download")
                self.handlePremium()

            else:
                self.logDebug("Handled as free download")
                self.handleFree()

        self.downloadLink(self.link)
        self.checkFile()


    def handlePremium(self):
        return self.handleFree()


    def handleFree(self):
        if self.premium:
            raise NotImplementedError
        else:
            self.logError(_("Required account not found"))
