# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class Premium4Me(MultiHoster):
    __name__ = "Premium4Me"
    __type__ = "hook"
    __version__ = "0.03"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description__ = """Premium.to hook plugin"""
    __author_name__ = ("RaNaN", "zoidberg", "stickell")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def getHoster(self):
        page = getURL("http://premium.to/api/hosters.php?authcode=%s" % self.account.authcode)
        return [x.strip() for x in page.replace("\"", "").split(";")]

    def coreReady(self):
        self.account = self.core.accountManager.getAccountPlugin("Premium4Me")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError(_("Please add your premium.to account first and restart pyLoad"))
            return

        return MultiHoster.coreReady(self)
