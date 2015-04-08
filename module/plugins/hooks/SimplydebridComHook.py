# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class SimplydebridComHook(MultiHook):
    __name__    = "SimplydebridComHook"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Simply-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def getHosters(self):
        html = self.getURL("http://simply-debrid.com/api.php", get={'list': 1})
        return [x.strip() for x in html.rstrip(';').replace("\"", "").split(";")]
