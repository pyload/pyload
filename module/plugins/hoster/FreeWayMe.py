# -*- coding: utf-8 -*-

from module.plugins.Hoster import Hoster


class FreeWayMe(Hoster):
    __name__ = "FreeWayMe"
    __type__ = "hoster"
    __version__ = "0.11"

    __pattern__ = r'https://(?:www\.)?free-way.me/.*'

    __description__ = """FreeWayMe hoster plugin"""
    __author_name__ = "Nicolas Giese"
    __author_mail__ = "james@free-way.me"


    def setup(self):
        self.resumeDownload = False
        self.chunkLimit = 1
        self.multiDL = self.premium

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "FreeWayMe")
            self.fail("No FreeWay account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        (user, data) = self.account.selectAccount()

        self.download(
            "https://www.free-way.me/load.php",
            get={"multiget": 7, "url": pyfile.url, "user": user, "pw": self.account.getpw(user), "json": ""},
            disposition=True)
