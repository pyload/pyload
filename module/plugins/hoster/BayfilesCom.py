# -*- coding: utf-8 -*-

import re

from time import time

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BayfilesCom(SimpleHoster):
    __name__ = "BayfilesCom"
    __type__ = "hoster"
    __version__ = "0.07"

    __pattern__ = r'https?://(?:www\.)?bayfiles\.(com|net)/file/(?P<ID>[a-zA-Z0-9]+/[a-zA-Z0-9]+/[^/]+)'

    __description__ = """Bayfiles.com hoster plugin"""
    __author_name__ = ("zoidberg", "Walter Purcaro")
    __author_mail__ = ("zoidberg@mujmail.cz", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'<p title="(?P<N>[^"]+)">[^<]*<strong>(?P<S>[0-9., ]+)(?P<U>[kKMG])i?B</strong></p>'
    OFFLINE_PATTERN = r'(<p>The requested file could not be found.</p>|<title>404 Not Found</title>)'

    WAIT_PATTERN = r'>Your IP [0-9.]* has recently downloaded a file\. Upgrade to premium or wait (\d+) minutes\.<'
    VARS_PATTERN = r'var vfid = (\d+);\s*var delay = (\d+);'
    FREE_LINK_PATTERN = r"javascript:window.location.href = '([^']+)';"
    PREMIUM_LINK_PATTERN = r'(?:<a class="highlighted-btn" href="|(?=http://s\d+\.baycdn\.com/dl/))(.*?)"'


    def handleFree(self):
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(int(m.group(1)) * 60)
            self.retry()

        # Get download token
        m = re.search(self.VARS_PATTERN, self.html)
        if m is None:
            self.parseError('VARS')
        vfid, delay = m.groups()

        response = json_loads(self.load('http://bayfiles.com/ajax_download', get={
            "_": time() * 1000,
            "action": "startTimer",
            "vfid": vfid}, decode=True))

        if not "token" in response or not response['token']:
            self.fail('No token')

        self.wait(int(delay))

        self.html = self.load('http://bayfiles.com/ajax_download', get={
            "token": response['token'],
            "action": "getLink",
            "vfid": vfid})

        # Get final link and download
        m = re.search(self.FREE_LINK_PATTERN, self.html)
        if m is None:
            self.parseError("Free link")
        self.startDownload(m.group(1))

    def handlePremium(self):
        m = re.search(self.PREMIUM_LINK_PATTERN, self.html)
        if m is None:
            self.parseError("Premium link")
        self.startDownload(m.group(1))

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
