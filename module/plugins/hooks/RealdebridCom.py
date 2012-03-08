# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class RealdebridCom(MultiHoster):
    __name__ = "RealdebridCom"
    __version__ = "0.41"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("https", "bool", "Enable HTTPS", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    replacements = [("freakshare.net", "freakshare.com")]

    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://real-debrid.com/api/hosters.php").replace("\"","").strip()

        hosters = set([x.strip() for x in page.split(",") if x.strip()])
        
        configMode = self.getConfig('hosterListMode')
        if configMode in ("listed", "unlisted"):
            configList = set(self.getConfig('hosterList').strip().lower().replace('|',',').replace(';',',').split(','))
            configList.discard(u'')
            if configMode == "listed":
                hosters &= configList
            else:
                hosters -= configList
        
        return list(hosters)
