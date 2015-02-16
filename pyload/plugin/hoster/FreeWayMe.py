# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHoster import MultiHoster


class FreeWayMe(MultiHoster):
    __name    = "FreeWayMe"
    __type    = "hoster"
    __version = "0.16"

    __pattern = r'https://(?:www\.)?free-way\.me/.+'

    __description = """FreeWayMe multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Nicolas Giese", "james@free-way.me")]


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
                                    'json'    : ""},
                               just_header=True)

            if 'location' in header:
                headers = self.load(header['location'], just_header=True)
                if headers['code'] == 500:
                    # error on 2nd stage
                    self.logError(_("Error [stage2]"))
                else:
                    # seems to work..
                    self.download(header['location'])
                    break
            else:
                # error page first stage
                self.logError(_("Error [stage1]"))

            #@TODO: handle errors
