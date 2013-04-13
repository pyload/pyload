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


class MultiDebridCom(MultiHoster):
    __name__ = "MultiDebridCom"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Multi-debrid.com hook plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def getHoster(self):
        json_data = getURL('http://multi-debrid.com/api.php?hosts', decode=True)
        self.logDebug('JSON data: ' + json_data)
        json_data = json_loads(json_data)

        return json_data['hosts']
