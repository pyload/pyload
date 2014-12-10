# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class NosuploadCom(XFSHoster):
    __name    = "NosuploadCom"
    __type    = "hoster"
    __version = "0.31"

    __pattern = r'http://(?:www\.)?nosupload\.com/\?d=\w{12}'

    __description = """Nosupload.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("igel", "igelkun@myopera.com")]


    HOSTER_DOMAIN = "nosupload.com"

    SIZE_PATTERN = r'<p><strong>Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>'
    LINK_PATTERN = r'<a class="select" href="(http://.+?)">Download</a>'
    WAIT_PATTERN = r'Please wait.*?>(\d+)</span>'


    def getDownloadLink(self):
        # stage1: press the "Free Download" button
        data = self.getPostParameters()
        self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)

        # stage2: wait some time and press the "Download File" button
        data = self.getPostParameters()
        wait_time = re.search(self.WAIT_PATTERN, self.html, re.M | re.S).group(1)
        self.logDebug("Hoster told us to wait %s seconds" % wait_time)
        self.wait(wait_time)
        self.html = self.load(self.pyfile.url, post=data, ref=True, decode=True)

        # stage3: get the download link
        return re.search(self.LINK_PATTERN, self.html, re.S).group(1)


getInfo = create_getInfo(NosuploadCom)
