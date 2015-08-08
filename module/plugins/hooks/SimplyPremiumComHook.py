# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class SimplyPremiumComHook(MultiHook):
    __name__    = "SimplyPremiumComHook"
    __type__    = "hook"
    __version__ = "0.06"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Simply-Premium.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def get_hosters(self):
        json_data = self.load("http://www.simply-premium.com/api/hosts.php", get={'format': "json", 'online': 1})
        json_data = json_loads(json_data)

        host_list = [element['regex'] for element in json_data['result']]

        return host_list
