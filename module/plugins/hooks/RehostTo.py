# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RehostTo(MultiHook):
    __name__    = "RehostTo"
    __type__    = "hook"
    __version__ = "0.45"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Rehost.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def getHosters(self):
        page = self.getURL("http://rehost.to/api.php",
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

        return MultiHook.coreReady(self)
