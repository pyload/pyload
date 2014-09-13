# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class RPNetBiz(MultiHoster):
    __name__ = "RPNetBiz"
    __type__ = "hook"
    __version__ = "0.1"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """RPNet.biz hook plugin"""
    __author_name__ = "Dman"
    __author_mail__ = "dmanugm@gmail.com"


    def getHoster(self):
        # No hosts supported if no account
        if not self.account or not self.account.canUse():
            return []

        # Get account data
        (user, data) = self.account.selectAccount()

        response = getURL("https://premium.rpnet.biz/client_api.php",
                          get={"username": user, "password": data['password'], "action": "showHosterList"})
        hoster_list = json_loads(response)

        # If account is not valid thera are no hosters available
        if 'error' in hoster_list:
            return []

        # Extract hosters from json file
        return hoster_list['hosters']

    def coreReady(self):
        # Get account plugin and check if there is a valid account available
        self.account = self.core.accountManager.getAccountPlugin("RPNetBiz")
        if not self.account.canUse():
            self.account = None
            self.logError(_("Please enter your %s account or deactivate this plugin") % "rpnet")
            return

        # Run the overwriten core ready which actually enables the multihoster hook
        return MultiHoster.coreReady(self)
