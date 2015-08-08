# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class FastixRuHook(MultiHook):
    __name__    = "FastixRuHook"
    __type__    = "hook"
    __version__ = "0.06"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Fastix.ru hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def get_hosters(self):
        html = self.load("http://fastix.ru/api_v2",
                      get={'apikey': "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                           'sub'   : "allowed_sources"})
        host_list = json_loads(html)
        host_list = host_list['allow']
        return host_list
