# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class UnrestrictLi(MultiHook):
    __name    = "UnrestrictLi"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   ),
                  ("history"       , "bool"               , "Delete History"                      , False)]

    __description = """Unrestrict.li hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://unrestrict.li/api/jdownloader/hosts.php", get={'format': "json"})
        json_data = json_loads(json_data)

        return [element['host'] for element in json_data['result']]
