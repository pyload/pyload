# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.MultiHoster import MultiHoster


class UnrestrictLi(MultiHoster):
    __name    = "UnrestrictLi"
    __type    = "hook"
    __version = "0.02"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24),
                ("history", "bool", "Delete History", False)]

    __description = """Unrestrict.li hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def getHoster(self):
        json_data = getURL("http://unrestrict.li/api/jdownloader/hosts.php", get={'format': "json"})
        json_data = json_loads(json_data)

        host_list = [element['host'] for element in json_data['result']]

        return host_list
