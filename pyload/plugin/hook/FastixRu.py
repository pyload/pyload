# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class FastixRu(MultiHook):
    __name__    = "FastixRu"
    __type__    = "hook"
    __version__ = "0.05"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Fastix.ru hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def getHosters(self):
        html = self.getURL("http://fastix.ru/api_v2",
                      get={'apikey': "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                           'sub'   : "allowed_sources"})
        host_list = json_loads(html)
        host_list = host_list['allow']
        return host_list
