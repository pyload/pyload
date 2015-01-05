# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class SmoozedCom(MultiHook):
    __name__    = "SmoozedCom"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Smoozed.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = []


    def getHosters(self):
        # If no accounts are available there will be no hosters available
        if not self.account or not self.account.canUse():
            return []

        # Get account data
        (user, data) = self.account.selectAccount()
        account_info = self.account.getAccountInfo(user, True)

        # Return hoster list
        return account_info["hoster"]


    def coreReady(self):
        # Get account plugin and check if there is a valid account available
        self.account = self.core.accountManager.getAccountPlugin("SmoozedCom")
        if not self.account.canUse():
            self.account = None
            self.logError(_("Please add a valid premiumize.me account first and restart pyLoad"))
            return

        # Run the overwriten core ready which actually enables the multihook hook
        return MultiHook.coreReady(self)
