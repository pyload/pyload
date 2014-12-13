# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.MultiHoster import MultiHoster


class PremiumTo(MultiHoster):
    __name    = "PremiumTo"
    __type    = "hook"
    __version = "0.04"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description = """Premium.to hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]



    def getHoster(self):
        page = getURL("http://premium.to/api/hosters.php",
                      get={'username': self.account.username, 'password': self.account.password})
        return [x.strip() for x in page.replace("\"", "").split(";")]


    def activate(self):
        self.account = self.core.accountManager.getAccountPlugin("PremiumTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError(_("Please add your premium.to account first and restart pyLoad"))
            return

        return MultiHoster.activate(self)
