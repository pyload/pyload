# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class OverLoadMeHook(MultiHook):
    __name__    = "OverLoadMeHook"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("ssl"           , "bool"               , "Use HTTPS"                           , True )]

    __description__ = """Over-Load.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def getHosters(self):
        https = "https" if self.getConfig('ssl') else "http"
        html = self.getURL(https + "://api.over-load.me/hoster.php",
                      get={'auth': "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"}).replace("\"", "").strip()
        self.logDebug("Hosterlist", html)

        return [x.strip() for x in html.split(",") if x.strip()]
