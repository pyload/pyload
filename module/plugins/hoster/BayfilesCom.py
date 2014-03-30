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

    @author: zoidberg
"""

import re
from time import time

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.common.json_layer import json_loads


class BayfilesCom(SimpleHoster):
    __name__ = "BayfilesCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?bayfiles\.(com|net)/file/(?P<ID>[a-zA-Z0-9]+/[a-zA-Z0-9]+/[^/]+)"
    __version__ = "0.06"
    __description__ = """Bayfiles.com hoster plugin"""
    __author_name__ = ("zoidberg", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<p title="(?P<N>[^"]+)">[^<]*<strong>(?P<S>[0-9., ]+)(?P<U>[kKMG])i?B</strong></p>'
    FILE_OFFLINE_PATTERN = r'(<p>The requested file could not be found.</p>|<title>404 Not Found</title>)'

    WAIT_PATTERN = r'>Your IP [0-9.]* has recently downloaded a file\. Upgrade to premium or wait (\d+) minutes\.<'
    VARS_PATTERN = r'var vfid = (\d+);\s*var delay = (\d+);'
    LINK_PATTERN = r"javascript:window.location.href = '([^']+)';"
    PREMIUM_LINK_PATTERN = r'(?:<a class="highlighted-btn" href="|(?=http://s\d+\.baycdn\.com/dl/))(.*?)"'

    def handleFree(self):
        found = re.search(self.WAIT_PATTERN, self.html)
        if found:
            self.wait(int(found.group(1)) * 60)
            self.retry()

        # Get download token
        found = re.search(self.VARS_PATTERN, self.html)
        if not found:
            self.parseError('VARS')
        vfid, delay = found.groups()

        response = json_loads(self.load('https://bayfiles.com/ajax_download', get={
            "_": time() * 1000,
            "action": "startTimer",
            "vfid": vfid}, decode=True))

        if not "token" in response or not response['token']:
            self.fail('No token')

        self.wait(int(delay))

        self.html = self.load('https://bayfiles.com/ajax_download', get={
            "token": response['token'],
            "action": "getLink",
            "vfid": vfid})

        # Get final link and download
        found = re.search(self.LINK_PATTERN, self.html)
        if not found:
            self.parseError("Free link")
        self.startDownload(found.group(1))

    def handlePremium(self):
        found = re.search(self.PREMIUM_LINK_PATTERN, self.html)
        if not found:
            self.parseError("Premium link")
        self.startDownload(found.group(1))

    def startDownload(self, url):
        self.logDebug("%s URL: %s" % ("Premium" if self.premium else "Free", url))
        self.download(url)
        # check download
        check = self.checkDownload({
            "waitforfreeslots": re.compile(r"<title>BayFiles</title>"),
            "notfound": re.compile(r"<title>404 Not Found</title>")
        })
        if check == "waitforfreeslots":
            self.retry(30, 5 * 60, "Wait for free slot")
        elif check == "notfound":
            self.retry(30, 5 * 60, "404 Not found")


getInfo = create_getInfo(BayfilesCom)
