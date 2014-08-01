# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class MegaDebridEu(MultiHoster):
    __name__ = "MegaDebridEu"
    __type__ = "hook"
    __version__ = "0.02"

    __config__ = [("activated", "bool", "Activated", False),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False)]

    __description__ = """mega-debrid.eu hook plugin"""
    __author_name__ = "D.Ducatel"
    __author_mail__ = "dducatel@je-geek.fr"


    def getHoster(self):
        reponse = getURL('http://www.mega-debrid.eu/api.php?action=getHosters')
        json_data = json_loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.logError("Unable to retrieve hoster list")
            host_list = list()

        return host_list
