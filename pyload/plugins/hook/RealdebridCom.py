# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class RealdebridCom(MultiHoster):
    __name    = "RealdebridCom"
    __type    = "hook"
    __version = "0.43"

    __config = [("https", "bool", "Enable HTTPS", False),
                ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """Real-Debrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://real-debrid.com/api/hosters.php").replace("\"", "").strip()

        return [x.strip() for x in page.split(",") if x.strip()]
