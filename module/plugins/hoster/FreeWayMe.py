# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class FreeWayMe(MultiHoster):
    __name__    = "FreeWayMe"
    __type__    = "hoster"
    __version__ = "0.16"

    __pattern__ = r'https://(?:www\.)?free-way\.me/.+'

    __description__ = """FreeWayMe multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = self.premium
        self.chunkLimit     = 1


    def handlePremium(self, pyfile):
        user, data = self.account.selectAccount()

        for _i in xrange(5):
            # try it five times
            header = self.load("https://www.free-way.me/load.php",
                      get={'multiget': 7,
                           'url'     : pyfile.url,
                           'user'    : user,
                           'pw'      : self.account.getAccountData(user)['password'],
                           'json'    : ""}, just_header=True)
            if "location" in header:
                #download
                self.logInfo("Download: " + header['location'])
                headers = self.load(header['location'],just_header=True)
                if headers['code'] == 500:
                    #error on 2nd stage
                    self.logInfo("Free-Way Error [stage2]")
                    # todo: handle errors
                else:
                    # seems to work..
                    self.download(header['location'])
                    break
            else:
                #error page first stage
                self.logInfo("Free-Way Error [stage1]")
                # todo: handle errors


getInfo = create_getInfo(FreeWayMe)
