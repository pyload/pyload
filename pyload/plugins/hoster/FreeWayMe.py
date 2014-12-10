# -*- coding: utf-8 -*-

from pyload.plugins.Hoster import Hoster


class FreeWayMe(Hoster):
    __name__    = "FreeWayMe"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'https://(?:www\.)?free-way\.me/.*'

    __description__ = """FreeWayMe hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = self.premium
        self.chunkLimit     = 1


    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "FreeWayMe")
            self.fail(_("No FreeWay account provided"))

        self.logDebug("Old URL: %s" % pyfile.url)

        (user, data) = self.account.selectAccount()

        self.download(
            "https://www.free-way.me/load.php",
            get={"multiget": 7, "url": pyfile.url, "user": user, "pw": self.account.getpw(user), "json": ""},
            disposition=True)
