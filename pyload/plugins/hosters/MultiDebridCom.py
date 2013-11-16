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

from pyload.plugins.Hoster import Hoster
from pyload.utils import json_loads


class MultiDebridCom(Hoster):
    __name__ = "MultiDebridCom"
    __version__ = "0.02"
    __type__ = "hoster"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]
    __pattern__ = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/"
    __description__ = """Multi-debrid.com hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def init(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Multi-debrid.com")
            self.fail("No Multi-debrid.com account provided")

        self.logDebug("Original URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            page = self.req.load('http://multi-debrid.com/api.php',
                                 get={'user': self.user, 'pass': self.account.getAccountData(self.user)['password'],
                                      'link': pyfile.url})
            self.logDebug("JSON data: " + page)
            page = json_loads(page)
            if page['status'] != 'ok':
                self.fail('Unable to unrestrict link')
            new_url = page['link']

        self.logDebug("Unrestricted URL: " + new_url)

        self.download(new_url, disposition=True)
