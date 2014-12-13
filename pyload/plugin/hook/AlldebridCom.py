# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.MultiHoster import MultiHoster


class AlldebridCom(MultiHoster):
    __name    = "AlldebridCom"
    __type    = "hook"
    __version = "0.13"

    __config = [("https", "bool", "Enable HTTPS", False),
                ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """Alldebrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Andy Voigt", "spamsales@online.de")]


    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://www.alldebrid.com/api.php", get={'action': "get_host"}).replace("\"", "").strip()

        return [x.strip() for x in page.split(",") if x.strip()]
