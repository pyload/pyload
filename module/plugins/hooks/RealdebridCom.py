# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RealdebridCom(MultiHook):
    __name__    = "RealdebridCom"
    __type__    = "hook"
    __version__ = "0.45"

    __config__ = [("https", "bool", "Enable HTTPS", False),
                  ("mode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Real-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def getHosters(self):
        https = "https" if self.getConfig("https") else "http"
        page = self.getURL(https + "://real-debrid.com/api/hosters.php").replace("\"", "").strip()

        return [x.strip() for x in page.split(",") if x.strip()]
