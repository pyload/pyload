# -*- coding: utf-8 -*-

from pyload.plugin.Hoster import Hoster


class ZeveraCom(Hoster):
    __name    = "ZeveraCom"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?zevera\.com/.*'

    __description = """Zevera.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True
        self.chunkLimit     = 1


    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "zevera.com")
            self.fail(_("No zevera.com account provided"))

        self.logDebug("Old URL: %s" % pyfile.url)

        if self.account.getAPIData(self.req, cmd="checklink", olink=pyfile.url) != "Alive":
            self.fail(_("Offline or not downloadable - contact Zevera support"))

        header = self.account.getAPIData(self.req, just_header=True, cmd="generatedownloaddirect", olink=pyfile.url)
        if not "location" in header:
            self.fail(_("Unable to initialize download"))

        self.download(header['location'], disposition=True)

        check = self.checkDownload({"error": 'action="ErrorDownload.aspx'})
        if check == "error":
            self.fail(_("Error response received - contact Zevera support"))
