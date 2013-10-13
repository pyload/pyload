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
from datetime import datetime, timedelta

from module.plugins.Hoster import Hoster
from module.common.json_layer import json_loads


def secondsToMidnight():
    # Seconds until 00:10 GMT+2
    now = datetime.utcnow() + timedelta(hours=2)
    if now.hour is 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + timedelta(days=1)
    midnight = midnight.replace(hour=0, minute=10, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


class UnrestrictLi(Hoster):
    __name__ = "UnrestrictLi"
    __version__ = "0.11"
    __type__ = "hoster"
    __pattern__ = r"https?://.*(unrestrict|unr)\.li"
    __description__ = """Unrestrict.li hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def setup(self):
        self.chunkLimit = 16
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Unrestrict.li")
            self.fail("No Unrestrict.li account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            for i in xrange(5):
                page = self.req.load('https://unrestrict.li/unrestrict.php',
                                     post={'link': pyfile.url, 'domain': 'long'})
                self.logDebug("JSON data: " + page)
                if page != '':
                    break
            else:
                self.logInfo("Unable to get API data, waiting 1 minute and retry")
                self.retry(5, 60, "Unable to get API data")

            if 'Expired session' in page or ("You are not allowed to "
                                             "download from this host" in page and self.premium):
                self.account.relogin(self.user)
                self.retry()
            elif "File offline" in page:
                self.offline()
            elif "You are not allowed to download from this host" in page:
                self.fail("You are not allowed to download from this host")
            elif "You have reached your daily limit for this host" in page:
                self.logInfo("Reached daily limit for this host. Waiting until 00:10 GMT+2")
                self.retry(5, secondsToMidnight(), "Daily limit for this host reached")
            elif "ERROR_HOSTER_TEMPORARILY_UNAVAILABLE" in page:
                self.logInfo("Hoster temporarily unavailable, waiting 1 minute and retry")
                self.retry(5, 60, "Hoster is temporarily unavailable")
            page = json_loads(page)
            new_url = page.keys()[0]
            self.api_data = page[new_url]

        if new_url != pyfile.url:
            self.logDebug("New URL: " + new_url)

        if hasattr(self, 'api_data'):
            self.setNameSize()

        self.download(new_url, disposition=True)

        if self.getConfig("history"):
            self.load("https://unrestrict.li/history/&delete=all")
            self.logInfo("Download history deleted")

    def setNameSize(self):
        if 'name' in self.api_data:
            self.pyfile.name = self.api_data['name']
        if 'size' in self.api_data:
            self.pyfile.size = self.api_data['size']
