# -*- coding: utf-8 -*-
############################################################################
# This program is free software: you can redistribute it and/or modify     #
# it under the terms of the GNU Affero General Public License as           #
# published by the Free Software Foundation, either version 3 of the       #
# License, or (at your option) any later version.                          #
#                                                                          #
# This program is distributed in the hope that it will be useful,          #
# but WITHOUT ANY WARRANTY; without even the implied warranty of           #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
# GNU Affero General Public License for more details.                      #
#                                                                          #
# You should have received a copy of the GNU Affero General Public License #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
############################################################################

from module.plugins.internal.MultiHoster import MultiHoster
from module.network.RequestFactory import getURL
from module.common.json_layer import json_loads


class MegaDebridEu(MultiHoster):
    __name__ = "MegaDebridEu"
    __version__ = "0.02"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False)]
    __description__ = """mega-debrid.eu hook plugin"""
    __author_name__ = "D.Ducatel"
    __author_mail__ = "dducatel@je-geek.fr"

    def getHoster(self):
        reponse = getURL('http://www.mega-debrid.eu/api.php?action=getHosters')
        json_data = json_loads(reponse)

        if json_data["response_code"] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.logError("Unable to retrieve hoster list")
            host_list = list()

        return host_list
