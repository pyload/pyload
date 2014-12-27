# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class PremiumTo(MultiHook):
    __name__    = "PremiumTo"
    __type__    = "hook"
    __version__ = "0.06"

    __config__ = [("mode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", "")]

    __description__ = """Premium.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        page = self.getURL("http://premium.to/api/hosters.php",
                      get={'username': self.account.username, 'password': self.account.password})
        return [x.strip() for x in page.replace("\"", "").split(";")]


    def coreReady(self):
        self.account = self.core.accountManager.getAccountPlugin("PremiumTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError(_("Please add your premium.to account first and restart pyLoad"))
            return

        return MultiHook.coreReady(self)
