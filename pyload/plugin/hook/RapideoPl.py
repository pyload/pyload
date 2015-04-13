# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class RapideoPl(MultiHook):
    __name    = "RapideoPl"
    __type    = "hook"
    __version = "0.03"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Rapideo.pl hook plugin"""
    __license     = "GPLv3"
    __authors     = [("goddie", "dev@rapideo.pl")]


    def getHosters(self):
        hostings         = json_loads(self.getURL("https://www.rapideo.pl/clipboard.php?json=3").strip())
        hostings_domains = [domain for row in hostings for domain in row["domains"] if row["sdownload"] == "0"]

        self.logDebug(hostings_domains)

        return hostings_domains
