# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class SimplyPremiumCom(MultiHook):
    __name    = "SimplyPremiumCom"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Simply-Premium.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("EvolutionClip", "evolutionclip@live.de")]


    def getHosters(self):
        json_data = self.getURL("http://www.simply-premium.com/api/hosts.php", get={'format': "json", 'online': 1})
        json_data = json_loads(json_data)

        host_list = [element['regex'] for element in json_data['result']]

        return host_list
