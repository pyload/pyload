# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class RPNetBiz(MultiHook):
    __name__    = "RPNetBiz"
    __type__    = "hook"
    __version__ = "0.12"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """RPNet.biz hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Dman", "dmanugm@gmail.com")]


    def getHosters(self):
        # No hosts supported if no account
        if not self.account or not self.account.canUse():
            return []

        # Get account data
        (user, data) = self.account.selectAccount()

        res = self.getURL("https://premium.rpnet.biz/client_api.php",
                     get={'username': user, 'password': data['password'], 'action': "showHosterList"})
        hoster_list = json_loads(res)

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
        return MultiHook.coreReady(self)
