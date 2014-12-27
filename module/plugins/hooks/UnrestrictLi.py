# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class UnrestrictLi(MultiHook):
    __name__    = "UnrestrictLi"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24),
                  ("history", "bool", "Delete History", False)]

    __description__ = """Unrestrict.li hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://unrestrict.li/api/jdownloader/hosts.php", get={'format': "json"})
        json_data = json_loads(json_data)

        host_list = [element['host'] for element in json_data['result']]

        return host_list
