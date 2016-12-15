# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.plugins.internal.multihoster import MultiHoster
from pyload.common.json_layer import json_loads
from pyload.network.requestfactory import get_url


class RPNetBiz(MultiHoster):
    __name__ = "RPNetBiz"
    __version__ = "0.1"
    __type__ = "hook"
    __description__ = """RPNet.biz hook plugin"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]
    __author_name__ = "Dman"
    __author_mail__ = "dmanugm@gmail.com"

    def get_hoster(self):
        # No hosts supported if no account
        if not self.account or not self.account.canUse():
            return []

        # Get account data
        (user, data) = self.account.selectAccount()

        response = get_url("https://premium.rpnet.biz/client_api.php",
                          get={"username": user, "password": data['password'], "action": "showHosterList"})
        hoster_list = json_loads(response)

        # If account is not valid thera are no hosters available
        if 'error' in hoster_list:
            return []

        # Extract hosters from json file
        return hoster_list['hosters']

    def core_ready(self):
        # Get account plugin and check if there is a valid account available
        self.account = self.pyload.accountmanager.get_account_plugin("RPNetBiz")
        if not self.account.canUse():
            self.account = None
            self.logError(_("Please enter your %s account or deactivate this plugin") % "rpnet")
            return

        # Run the overwriten core ready which actually enables the multihoster hook
        return MultiHoster.coreReady(self)
