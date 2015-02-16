# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class FreeWayMe(MultiHook):
    __name__    = "FreeWayMe"
    __type__    = "hook"
    __version__ = "0.14"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """FreeWay.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def getHosters(self):
        hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={'id': 3}).replace("\"", "").strip()
        self.logDebug("Hosters", hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
