# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class Premium4Me(MultiHoster):
    __name__ = "Premium4Me"
    __version__ = "0.02"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
        ("hosterListMode", "all;listed;unlisted", "Use for downloads from supported hosters:", "all"),
        ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """premium4.me hook plugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    replacements = [("freakshare.net", "freakshare.com")]

    def getHoster(self):

        page = getURL("http://premium4.me/api/hosters.php?authcode=%s" % self.account.authcode)
        hosters = set([x.strip() for x in page.replace("\"", "").split(";")])
        
        configMode = self.getConfig('hosterListMode')
        if configMode in ("listed", "unlisted"):
            configList = set(self.getConfig('hosterList').strip().lower().replace(',','|').split('|'))
            configList.discard(u'')
            if configMode == "listed":
                hosters &= configList
            elif configMode == "unlisted":
                hosters -= configList
        
        return list(hosters)

    def coreReady(self):

        self.account = self.core.accountManager.getAccountPlugin("Premium4Me")

        user = self.account.selectAccount()[0]

        if not user:
            self.logError(_("Please add your premium4.me account first and restart pyLoad"))
            return

        return MultiHoster.coreReady(self)