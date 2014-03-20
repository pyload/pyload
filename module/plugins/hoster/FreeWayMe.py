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

from module.plugins.Hoster import Hoster

class FreeWayMe(Hoster):
    __name__ = "FreeWayMe"
    __version__ = "0.11"
    __type__ = "hoster"
    __pattern__ = r"https://free-way.me/.*"
    __description__ = """FreeWayMe hoster plugin"""
    __author_name__ = ("Nicolas Giese")
    __author_mail__ = ("james@free-way.me")

    def setup(self):
        self.resumeDownload = False
        self.chunkLimit = 1
        self.multiDL = self.premium

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "FreeWayMe")
            self.fail("No FreeWay account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        (user, data) = self.account.selectAccount()

        self.download(
            "https://www.free-way.me/load.php",
            get={"multiget": 7, "url": pyfile.url, "user": user, "pw": self.account.getpw(user), "json": ""},
            disposition=True)
