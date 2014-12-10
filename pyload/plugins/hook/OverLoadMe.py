# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class OverLoadMe(MultiHoster):
    __name    = "OverLoadMe"
    __type    = "hook"
    __version = "0.01"

    __config = [("https", "bool", "Enable HTTPS", True),
                ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 12)]

    __description = """Over-Load.me hook plugin"""
    __license     = "GPLv3"
    __authors     = [("marley", "marley@over-load.me")]


    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://api.over-load.me/hoster.php",
                      get={'auth': "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"}).replace("\"", "").strip()
        self.logDebug("Hosterlist", page)

        return [x.strip() for x in page.split(",") if x.strip()]
