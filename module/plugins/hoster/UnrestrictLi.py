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
    __version__ = "0.03"
    __type__ = "hoster"
    __pattern__ = r"https?://.*(unrestrict|unr)\.li"
    __description__ = """Unrestrict.li hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    def init(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError("Please enter your Unrestrict.li account or deactivate this plugin")
            self.fail("No Unrestrict.li account provided")

        self.logDebug("Old URL: %s" % pyfile.url)
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        else:
            for i in xrange(5):
                page = self.req.load('https://unrestrict.li/unrestrict.php',
                                     post={'link': pyfile.url, 'domain': 'long'})
                self.logDebug("JSON data: " + page)
                if page != '':
                    break
            if "You are not allowed to download from this host" in page:
                self.fail("You are not allowed to download from this host")
            elif "You have reached your daily limit for this host" in page:
                self.logInfo("Reached daily limit for this host. Waiting until 00:10 GMT+2")
                self.retry(5, secondsToMidnight(), "Daily limit for this host reached")
            page = json_loads(page)
            new_url = page.keys()[0]
            self.api_data = page[new_url]

        self.logDebug("New URL: " + new_url)

        self.download(new_url, disposition=True)

        if self.getConfig("history"):
            self.load("https://unrestrict.li/history/&delete=all")
            self.logInfo("Download history deleted")
