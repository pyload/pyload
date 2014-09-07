# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class MultiDebridCom(MultiHoster):
    __name__ = "MultiDebridCom"
    __type__ = "hook"
    __version__ = "0.01"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Multi-debrid.com hook plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


    def getHoster(self):
        json_data = getURL('http://multi-debrid.com/api.php?hosts', decode=True)
        self.logDebug('JSON data: ' + json_data)
        json_data = json_loads(json_data)

        return json_data['hosts']
