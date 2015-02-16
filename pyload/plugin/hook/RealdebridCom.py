# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class RealdebridCom(MultiHook):
    __name    = "RealdebridCom"
    __type    = "hook"
    __version = "0.46"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("ssl"           , "bool"               , "Use HTTPS"                           , True )]

    __description = """Real-Debrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def getHosters(self):
        https = "https" if self.getConfig("ssl") else "http"
        html = self.getURL(https + "://real-debrid.com/api/hosters.php").replace("\"", "").strip()

        return [x.strip() for x in html.split(",") if x.strip()]
