# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class MultihostersCom(Hoster):
    __name__ = "MultihostersCom"
    __version__ = "0.01"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?multihosters.com/.*'
    __description__ = """Multihosters.com hoster plugin"""
    __author_name__ = "tjeh"
    __author_mail__ = "tjeh@gmx.net"

    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(("Please enter your %s account or deactivate this plugin") % "multihosters.com")
            self.fail("No multihosters.com account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            new_url = "http://multihosters.com/getFiles.aspx?ourl=" + pyfile.url
            pyfile.url = new_url
            self.logDebug("New URL: %s" % new_url)

        if self.account.getAPIData(self.req, cmd="checklink", olink=pyfile.url) != "Alive":
            self.fail("Offline or not downloadable - contact Multihosters support")

        header = self.account.getAPIData(self.req, just_header=True, cmd="generatedownloaddirect", olink=pyfile.url)
        if not "location" in header:
            self.fail("Unable to initialize download - contact Multihosters support")
        self.download(header['location'], disposition=True)

        check = self.checkDownload({"error": 'action="ErrorDownload.aspx'})
        if check == "error":
            self.fail("Error response received - contact Multihosters support")
