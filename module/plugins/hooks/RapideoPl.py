# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook
from module.common.json_layer import json_loads as loads


class RapideoPl(MultiHook):
    __name__ = "RapideoPl"
    __version__ = "0.02"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Try standard download if download fails", False),
                  ("interval", "int", "Reload supported hosts interval in hours (0 to disable)", 24)]

    __description__ = "Rapideo.pl hook"
    __license__ = "GPLv3"
    __authors__ = [("goddie", "dev@rapideo.pl")]

    def getHosters(self):
        hostings = loads(self.getURL("https://www.rapideo.pl/clipboard.php?json=3").strip())
        hostings_domains = [domain for row in hostings for domain in row["domains"] if row["sdownload"] == "0"]
        self.logDebug(hostings_domains)
        return hostings_domains


