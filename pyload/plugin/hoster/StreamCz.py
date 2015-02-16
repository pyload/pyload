# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugin.Hoster import Hoster


def getInfo(urls):
    result = []

    for url in urls:

        html = getURL(url)
        if re.search(StreamCz.OFFLINE_PATTERN, html):
            # File offline
            result.append((url, 0, 1, url))
        else:
            result.append((url, 0, 2, url))
    yield result


class StreamCz(Hoster):
    __name    = "StreamCz"
    __type    = "hoster"
    __version = "0.20"

    __pattern = r'https?://(?:www\.)?stream\.cz/[^/]+/\d+'

    __description = """Stream.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<link rel="video_src" href="http://www\.stream\.cz/\w+/(\d+)-([^"]+)" />'
    OFFLINE_PATTERN = r'<h1 class="commonTitle">Str.nku nebylo mo.n. nal.zt \(404\)</h1>'

    CDN_PATTERN = r'<param name="flashvars" value="[^"]*&id=(?P<ID>\d+)(?:&cdnLQ=(?P<cdnLQ>\d*))?(?:&cdnHQ=(?P<cdnHQ>\d*))?(?:&cdnHD=(?P<cdnHD>\d*))?&'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        m = re.search(self.CDN_PATTERN, self.html)
        if m is None:
            self.error(_("CDN_PATTERN not found"))
        cdn = m.groupdict()
        self.logDebug(cdn)
        for cdnkey in ("cdnHD", "cdnHQ", "cdnLQ"):
            if cdnkey in cdn and cdn[cdnkey] > '':
                cdnid = cdn[cdnkey]
                break
        else:
            self.fail(_("Stream URL not found"))

        m = re.search(self.NAME_PATTERN, self.html)
        if m is None:
            self.error(_("NAME_PATTERN not found"))
        pyfile.name = "%s-%s.%s.mp4" % (m.group(2), m.group(1), cdnkey[-2:])

        download_url = "http://cdn-dispatcher.stream.cz/?id=" + cdnid
        self.logInfo(_("STREAM: %s") % cdnkey[-2:], download_url)
        self.download(download_url)
