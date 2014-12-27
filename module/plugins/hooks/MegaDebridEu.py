# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class MegaDebridEu(MultiHook):
    __name__    = "MegaDebridEu"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("revertfailed", "bool", "Revert to standard download if download fails", False)]

    __description__ = """mega-debrid.eu hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    def getHosters(self):
        reponse   = self.getURL("http://www.mega-debrid.eu/api.php", get={'action': "getHosters"})
        json_data = json_loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.logError(_("Unable to retrieve hoster list"))
            host_list = list()

        return host_list
