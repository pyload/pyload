# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class FastixRu(MultiHook):
    __name    = "FastixRu"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Fastix.ru hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def getHosters(self):
        html = self.getURL("http://fastix.ru/api_v2",
                      get={'apikey': "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                           'sub'   : "allowed_sources"})
        host_list = json_loads(html)
        host_list = host_list['allow']
        return host_list
