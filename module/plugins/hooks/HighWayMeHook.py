# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class HighWayMeHook(MultiHook):
    __name__    = "HighWayMeHook"
    __type__    = "hook"
    __version__ = "0.04"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """High-Way.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def get_hosters(self):
        json_data = json_loads(self.load("https://high-way.me/api.php",
                                           get={'hoster': 1}))
        return [element['name'] for element in json_data['hoster']]
