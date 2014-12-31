# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class AlldebridCom(MultiHook):
    __name__    = "AlldebridCom"
    __type__    = "hook"
    __version__ = "0.15"

    __config__ = [("https", "bool", "Enable HTTPS", False),
                  ("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Alldebrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def getHosters(self):
        https = "https" if self.getConfig("https") else "http"
        page = self.getURL(https + "://www.alldebrid.com/api.php", get={'action': "get_host"}).replace("\"", "").strip()

        return [x.strip() for x in page.split(",") if x.strip()]
