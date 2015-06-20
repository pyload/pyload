# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class MyfastfileComHook(MultiHook):
    __name__    = "MyfastfileComHook"
    __type__    = "hook"
    __version__ = "0.05"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Myfastfile.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://myfastfile.com/api.php", get={'hosts': ""}, decode=True)
        self.logDebug("JSON data", json_data)
        json_data = json_loads(json_data)

        return json_data['hosts']
