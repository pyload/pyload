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

import re
from urllib import unquote

from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads


class MegaDebridEu(Hoster):
    __name__ = "MegaDebridEu"
    __version__ = "0.2"
    __type__ = "hoster"
    __pattern__ = r'^https?://(?:w{3}\d+\.mega-debrid.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[^/]+/.+$'
    __description__ = """mega-debrid.eu hoster plugin"""
    __author_name__ = "D.Ducatel"
    __author_mail__ = "dducatel@je-geek.fr"

    # Define the base URL of MegaDebrid api
    API_URL = "https://www.mega-debrid.eu/api.php"

    def getFilename(self, url):
        try:
            return unquote(url.rsplit("/", 1)[1])
        except IndexError:
            return ""

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.exitOnFail(_("Please enter your %s account or deactivate this plugin") % "Mega-debrid.eu")
        else:
            if not self.connectToApi():
                self.exitOnFail(_("Impossible to connect to %s") % "Mega-debrid.eu")

            self.logDebug("Old URL: %s" % pyfile.url)
            new_url = self.debridLink(pyfile.url)
            self.logDebug("New URL: " + new_url)

        filename = self.getFilename(new_url)
        if filename != "":
            pyfile.name = filename
        self.download(new_url, disposition=True)

    def connectToApi(self):
        """
        Connexion to the mega-debrid API
        Return True if succeed
        """
        user, data = self.account.selectAccount()
        jsonResponse = self.load(self.API_URL,
                                 get={'action': 'connectUser', 'login': user, 'password': data["password"]})
        response = json_loads(jsonResponse)

        if response["response_code"] == "ok":
            self.token = response["token"]
            return True
        else:
            return False

    def debridLink(self, linkToDebrid):
        """
        Debrid a link
        Return The debrided link if succeed or original link if fail
        """
        jsonResponse = self.load(self.API_URL, get={'action': 'getLink', 'token': self.token},
                                 post={"link": linkToDebrid})
        response = json_loads(jsonResponse)

        if response["response_code"] == "ok":
            debridedLink = response["debridLink"][1:-1]
            return debridedLink
        else:
            self.exitOnFail(_("Impossible to debrid %s") % linkToDebrid)

    def exitOnFail(self, msg):
        """
        exit the plugin on fail case
        And display the reason of this failure
        """
        if self.getConfig("unloadFailing"):
            self.logError(msg)
            self.resetAccount()
        else:
            self.fail(msg)
