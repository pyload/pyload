# -*- coding: utf-8 -*-

# should be working

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class AlldebridCom(MultiHoster):
    __name__ = "AlldebridCom"
    __version__ = "0.13"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("https", "bool", "Enable HTTPS", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = ("Andy, Voigt")
    __author_mail__ = ("spamsales@online.de")

    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://www.alldebrid.com/api.php?action=get_host").replace("\"","").strip()
        
        return [x.strip() for x in page.split(",") if x.strip()]
