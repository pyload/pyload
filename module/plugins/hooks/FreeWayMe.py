# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: Nicolas Giese
"""

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class FreeWayMe(MultiHoster):
    __name__ = "FreeWayMe"
    __version__ = "0.11"
    __type__ = "hook"
    __description__ = """FreeWayMe hook plugin"""
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]
    __author_name__ = ("Nicolas Giese")
    __author_mail__ = ("james@free-way.me")

    def getHoster(self):
        hostis = getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3}).replace("\"", "").strip()
        self.logDebug("hosters: %s" % hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
