# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class NoPremiumPlHook(MultiHook):
    __name__    = "NoPremiumPlHook"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """NoPremium.pl hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("goddie", "dev@nopremium.pl")]


    def getHosters(self):
        hostings         = json_loads(self.getURL("https://www.nopremium.pl/clipboard.php?json=3").strip())
        hostings_domains = [domain for row in hostings for domain in row["domains"] if row["sdownload"] == "0"]

        self.logDebug(hostings_domains)

        return hostings_domains
