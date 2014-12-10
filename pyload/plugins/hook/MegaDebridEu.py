# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class MegaDebridEu(MultiHoster):
    __name    = "MegaDebridEu"
    __type    = "hook"
    __version = "0.02"

    __config = [("unloadFailing", "bool", "Revert to standard download if download fails", False)]

    __description = """mega-debrid.eu hook plugin"""
    __license     = "GPLv3"
    __authors     = [("D.Ducatel", "dducatel@je-geek.fr")]


    def getHoster(self):
        reponse   = getURL("http://www.mega-debrid.eu/api.php", get={'action': "getHosters"})
        json_data = json_loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.logError(_("Unable to retrieve hoster list"))
            host_list = list()

        return host_list
