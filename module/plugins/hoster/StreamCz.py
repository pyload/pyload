# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster


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
    __name__ = "StreamCz"
    __type__ = "hoster"
    __version__ = "0.2"

    __pattern__ = r'https?://(?:www\.)?stream\.cz/[^/]+/\d+.*'

    __description__ = """Stream.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<link rel="video_src" href="http://www.stream.cz/\w+/(\d+)-([^"]+)" />'
    OFFLINE_PATTERN = r'<h1 class="commonTitle">Str.nku nebylo mo.n. nal.zt \(404\)</h1>'

    CDN_PATTERN = r'<param name="flashvars" value="[^"]*&id=(?P<ID>\d+)(?:&cdnLQ=(?P<cdnLQ>\d*))?(?:&cdnHQ=(?P<cdnHQ>\d*))?(?:&cdnHD=(?P<cdnHD>\d*))?&'


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True

    def process(self, pyfile):

        self.html = self.load(pyfile.url, decode=True)

        if re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        m = re.search(self.CDN_PATTERN, self.html)
        if m is None:
            self.fail("Parse error (CDN)")
        cdn = m.groupdict()
        self.logDebug(cdn)
        for cdnkey in ("cdnHD", "cdnHQ", "cdnLQ"):
            if cdnkey in cdn and cdn[cdnkey] > '':
                cdnid = cdn[cdnkey]
                break
        else:
            self.fail("Stream URL not found")

        m = re.search(self.FILE_NAME_PATTERN, self.html)
        if m is None:
            self.fail("Parse error (NAME)")
        pyfile.name = "%s-%s.%s.mp4" % (m.group(2), m.group(1), cdnkey[-2:])

        download_url = "http://cdn-dispatcher.stream.cz/?id=" + cdnid
        self.logInfo("STREAM (%s): %s" % (cdnkey[-2:], download_url))
        self.download(download_url)
