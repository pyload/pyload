# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RealdebridCom(MultiHook):
    __name__    = "RealdebridCom"
    __type__    = "hook"
    __version__ = "0.46"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("ssl"           , "bool"               , "Use HTTPS"                           , True )]

    __description__ = """Real-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def getHosters(self):
        https = "https" if self.getConfig('ssl') else "http"
        html = self.getURL(https + "://real-debrid.com/api/hosters.php").replace("\"", "").strip()

        return [x.strip() for x in html.split(",") if x.strip()]
