# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class UnrestrictLi(MultiHook):
    __name__    = "UnrestrictLi"
    __type__    = "hook"
    __version__ = "0.05"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("history"       , "bool"               , "Delete History"                      , False)]

    __description__ = """Unrestrict.li hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://unrestrict.li/api/jdownloader/hosts.php", get={'format': "json"})
        json_data = json_loads(json_data)

        return [element['host'] for element in json_data['result']]
