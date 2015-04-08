# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class AlldebridComHook(MultiHook):
    __name__    = "AlldebridComHook"
    __type__    = "hook"
    __version__ = "0.16"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("ssl"           , "bool"               , "Use HTTPS"                           , True )]

    __description__ = """Alldebrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def getHosters(self):
        https = "https" if self.getConfig('ssl') else "http"
        html = self.getURL(https + "://www.alldebrid.com/api.php", get={'action': "get_host"}).replace("\"", "").strip()

        return [x.strip() for x in html.split(",") if x.strip()]
