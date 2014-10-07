# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster


class ZeveraCom(Hoster):
    __name__ = "ZeveraCom"
    __type__ = "hoster"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?zevera\.com/.*'

    __description__ = """Zevera.com hoster plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "zevera.com")
            self.fail("No zevera.com account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        if self.account.getAPIData(self.req, cmd="checklink", olink=pyfile.url) != "Alive":
            self.fail("Offline or not downloadable - contact Zevera support")

        header = self.account.getAPIData(self.req, just_header=True, cmd="generatedownloaddirect", olink=pyfile.url)
        if not "location" in header:
            self.fail("Unable to initialize download - contact Zevera support")

        self.download(header['location'], disposition=True)

        check = self.checkDownload({"error": 'action="ErrorDownload.aspx'})
        if check == "error":
            self.fail("Error response received - contact Zevera support")
