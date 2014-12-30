# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class OverLoadMe(MultiHook):
    __name__    = "OverLoadMe"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = [("https", "bool", "Enable HTTPS", True),
                  ("mode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 12)]

    __description__ = """Over-Load.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def getHosters(self):
        https = "https" if self.getConfig("https") else "http"
        page = self.getURL(https + "://api.over-load.me/hoster.php",
                      get={'auth': "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"}).replace("\"", "").strip()
        self.logDebug("Hosterlist", page)

        return [x.strip() for x in page.split(",") if x.strip()]
