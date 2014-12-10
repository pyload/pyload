# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class RehostTo(MultiHoster):
    __name    = "RehostTo"
    __type    = "hook"
    __version = "0.43"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """Rehost.to hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def getHoster(self):
        page = getURL("http://rehost.to/api.php",
                      get={'cmd': "get_supported_och_dl", 'long_ses': self.long_ses})
        return [x.strip() for x in page.replace("\"", "").split(",")]


    def coreReady(self):
        self.account = self.core.accountManager.getAccountPlugin("RehostTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError(_("Please add your rehost.to account first and restart pyLoad"))
            return

        data = self.account.getAccountInfo(user)
        self.ses = data['ses']
        self.long_ses = data['long_ses']

        return MultiHoster.coreReady(self)
