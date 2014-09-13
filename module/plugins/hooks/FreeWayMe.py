# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class FreeWayMe(MultiHoster):
    __name__ = "FreeWayMe"
    __type__ = "hook"
    __version__ = "0.11"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """FreeWay.me hook plugin"""
    __author_name__ = "Nicolas Giese"
    __author_mail__ = "james@free-way.me"


    def getHoster(self):
        hostis = getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3}).replace("\"", "").strip()
        self.logDebug("hosters: %s" % hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
