# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class FastixRu(MultiHook):
    __name__    = "FastixRu"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Fastix.ru hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def getHosters(self):
        page = self.getURL("http://fastix.ru/api_v2",
                      get={'apikey': "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                           'sub'   : "allowed_sources"})
        host_list = json_loads(page)
        host_list = host_list['allow']
        return host_list
