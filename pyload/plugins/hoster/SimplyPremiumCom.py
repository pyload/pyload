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


def secondsToMidnight():
    # Seconds until 00:10 GMT+2
    now = datetime.utcnow() + timedelta(hours=2)
    if now.hour is 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + timedelta(days=1)
    midnight = midnight.replace(hour=0, minute=10, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


class SimplyPremiumCom(Hoster):
    __name__ = "SimplyPremiumCom"
    __version__ = "0.01"
    __type__ = "hoster"
    __pattern__ = r"https?://.*(simply-premium)\.com"
    __description__ = """Simply-Premium.Com hoster plugin"""
    __author_name__ = ("EvolutionClip")
    __author_mail__ = ("evolutionclip@live.de")

    def setup(self):
        self.chunkLimit = 16
        self.resumeDownload = False

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Simply-Premium.com")
            self.fail("No Simply-Premium.com account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            for i in xrange(5):
                page = self.load('http://www.simply-premium.com/premium.php?info&link=' + pyfile.url)
                self.logDebug("JSON data: " + page)
                if page != '':
                    break
            else:
                self.logInfo("Unable to get API data, waiting 1 minute and retry")
                self.retry(5, 60, "Unable to get API data")

            if '<valid>0</valid>' in page or (
                    "You are not allowed to download from this host" in page and self.premium):
                self.account.relogin(self.user)
                self.retry()
            elif "NOTFOUND" in page:
                self.offline()
            elif "downloadlimit" in page:
                self.logInfo("Reached maximum connctions")
                self.retry(5, 60, "Reached maximum connctions")
            elif "trafficlimit" in page:
                self.logInfo("Reached daily limit for this host. Waiting until 00:10 GMT+2")
                self.retry(5, secondsToMidnight(), "Daily limit for this host reached")
            elif "hostererror" in page:
                self.logInfo("Hoster temporarily unavailable, waiting 1 minute and retry")
                self.retry(5, 60, "Hoster is temporarily unavailable")
            #page = json_loads(page)
            #new_url = page.keys()[0]
            #self.api_data = page[new_url]

            try:
                start = page.index('<name>') + len('<name>')
                end = page.index('</name>', start)
                self.pyfile.name = page[start:end]
            except ValueError:
                self.pyfile.name = ""

            try:
                start = page.index('<size>') + len('<size>')
                end = page.index('</size>', start)
                self.pyfile.size = int(float(page[start:end]))
            except ValueError:
                self.pyfile.size = 0

            new_url = 'http://www.simply-premium.com/premium.php?link=' + pyfile.url

        if new_url != pyfile.url:
            self.logDebug("New URL: " + new_url)

        self.download(new_url, disposition=True)
