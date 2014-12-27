# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class SimplyPremiumCom(MultiHook):
    __name__    = "SimplyPremiumCom"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Simply-Premium.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def getHosters(self):
        json_data = self.getURL("http://www.simply-premium.com/api/hosts.php", get={'format': "json", 'online': 1})
        json_data = json_loads(json_data)

        host_list = [element['regex'] for element in json_data['result']]

        return host_list
