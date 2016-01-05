# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Hoster import Hoster


class StreamCz(Hoster):
    __name__    = "StreamCz"
    __type__    = "hoster"
    __version__ = "0.25"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?stream\.cz/[^/]+/\d+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Stream.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<link rel="video_src" href="http://www\.stream\.cz/\w+/(\d+)-(.+?)" />'
    OFFLINE_PATTERN = r'<h1 class="commonTitle">Str.nku nebylo mo.n. nal.zt \(404\)</h1>'

    CDN_PATTERN = r'<param name="flashvars" value=".+?&id=(?P<ID>\d+)(?:&cdnLQ=(?P<cdnLQ>\d*))?(?:&cdnHQ=(?P<cdnHQ>\d*))?(?:&cdnHD=(?P<cdnHD>\d*))?&'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def process(self, pyfile):
        self.data = self.load(pyfile.url)

        if re.search(self.OFFLINE_PATTERN, self.data):
            self.offline()

        m = re.search(self.CDN_PATTERN, self.data)
        if m is None:
            self.error(_("CDN_PATTERN not found"))
        cdn = m.groupdict()
        self.log_debug(cdn)
        for cdnkey in ("cdnHD", "cdnHQ", "cdnLQ"):
            if cdnkey in cdn and cdn[cdnkey] > '':
                cdnid = cdn[cdnkey]
                break
        else:
            self.fail(_("Stream URL not found"))

        m = re.search(self.NAME_PATTERN, self.data)
        if m is None:
            self.error(_("NAME_PATTERN not found"))
        pyfile.name = "%s-%s.%s.mp4" % (m.group(2), m.group(1), cdnkey[-2:])

        download_url = "http://cdn-dispatcher.stream.cz/?id=" + cdnid
        self.log_info(_("STREAM: %s") % cdnkey[-2:], download_url)
        self.download(download_url)
