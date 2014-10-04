# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class SimplyPremiumCom(MultiHoster):
    __name__ = "SimplyPremiumCom"
    __type__ = "hook"
    __version__ = "0.02"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Simply-Premium.com hook plugin"""
    __author_name__ = "EvolutionClip"
    __author_mail__ = "evolutionclip@live.de"


    def getHoster(self):
        json_data = getURL('http://www.simply-premium.com/api/hosts.php?format=json&online=1')
        json_data = json_loads(json_data)

        host_list = [element['regex'] for element in json_data['result']]

        return host_list
