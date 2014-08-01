# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class PremiumizeMe(MultiHoster):
    __name__ = "PremiumizeMe"
    __type__ = "hook"
    __version__ = "0.12"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Premiumize.me hook plugin"""
    __author_name__ = "Florian Franzen"
    __author_mail__ = "FlorianFranzen@gmail.com"


    def getHoster(self):
        # If no accounts are available there will be no hosters available
        if not self.account or not self.account.canUse():
            return []

        # Get account data
        (user, data) = self.account.selectAccount()

        # Get supported hosters list from premiumize.me using the
        # json API v1 (see https://secure.premiumize.me/?show=api)
        answer = getURL("https://api.premiumize.me/pm-api/v1.php?method=hosterlist&params[login]=%s&params[pass]=%s" % (
                        user, data['password']))
        data = json_loads(answer)

        # If account is not valid thera are no hosters available
        if data['status'] != 200:
            return []

        # Extract hosters from json file
        return data['result']['hosterlist']

    def coreReady(self):
        # Get account plugin and check if there is a valid account available
        self.account = self.core.accountManager.getAccountPlugin("PremiumizeMe")
        if not self.account.canUse():
            self.account = None
            self.logError(_("Please add a valid premiumize.me account first and restart pyLoad."))
            return

        # Run the overwriten core ready which actually enables the multihoster hook
        return MultiHoster.coreReady(self)
