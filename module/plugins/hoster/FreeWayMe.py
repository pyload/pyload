# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FreeWayMe(SimpleHoster):
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


    def handleMulti(self):
        user, data = self.account.selectAccount()

        self.link = True
        self.download(
            "https://www.free-way.me/load.php",
            get={"multiget": 7, "url": self.pyfile.url, "user": user, "pw": self.account.getpw(user), "json": ""},
            disposition=True)


getInfo = create_getInfo(FreeWayMe)
