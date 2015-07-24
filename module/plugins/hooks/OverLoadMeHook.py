# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class OverLoadMeHook(MultiHook):
    __name__    = "OverLoadMeHook"
    __type__    = "hook"
    __version__ = "0.05"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Over-Load.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def get_hosters(self):
        html = self.load("https://api.over-load.me/hoster.php",
                         get={'auth': "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"}).replace("\"", "").strip()
        return [x.strip() for x in html.split(",") if x.strip()]
