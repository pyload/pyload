# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook
from pyload.utils import json_loads


class MyfastfileCom(MultiHook):
    __name    = "MyfastfileCom"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Myfastfile.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://myfastfile.com/api.php", get={'hosts': ""}, decode=True)
        self.logDebug("JSON data", json_data)
        json_data = json_loads(json_data)

        return json_data['hosts']
