# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class SimplydebridComHook(MultiHook):
    __name__    = "SimplydebridComHook"
    __type__    = "hook"
    __version__ = "0.05"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Simply-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def get_hosters(self):
        html = self.load("http://simply-debrid.com/api.php", get={'list': 1})
        return [x.strip() for x in html.rstrip(';').replace("\"", "").split(";")]
