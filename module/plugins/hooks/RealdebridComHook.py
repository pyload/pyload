# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RealdebridComHook(MultiHook):
    __name__    = "RealdebridComHook"
    __type__    = "hook"
    __version__ = "0.47"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Real-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def get_hosters(self):
        html = self.load("https://real-debrid.com/api/hosters.php").replace("\"", "").strip()
        return [x.strip() for x in html.split(",") if x.strip()]
