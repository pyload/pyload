# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.MultiHoster import MultiHoster


class FreeWayMe(MultiHoster):
    __name    = "FreeWayMe"
    __type    = "hook"
    __version = "0.11"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """FreeWay.me hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Nicolas Giese", "james@free-way.me")]


    def getHoster(self):
        hostis = getURL("https://www.free-way.me/ajax/jd.php", get={'id': 3}).replace("\"", "").strip()
        self.logDebug("Hosters", hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
