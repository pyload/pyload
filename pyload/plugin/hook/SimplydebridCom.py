# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class SimplydebridCom(MultiHook):
    __name    = "SimplydebridCom"
    __type    = "hook"
    __version = "0.04"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Simply-Debrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def getHosters(self):
        html = self.getURL("http://simply-debrid.com/api.php", get={'list': 1})
        return [x.strip() for x in html.rstrip(';').replace("\"", "").split(";")]
