# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class FreeWayMe(MultiHook):
    __name__    = "FreeWayMe"
    __type__    = "hook"
    __version__ = "0.13"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """FreeWay.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def getHosters(self):
        hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={'id': 3}).replace("\"", "").strip()
        self.logDebug("Hosters", hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
