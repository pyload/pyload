# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class NosuploadCom(XFSHoster):
    __name__    = "NosuploadCom"
    __type__    = "hoster"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?nosupload\.com/\?d=\w{12}'

    __description__ = """Nosupload.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com")]


    SIZE_PATTERN = r'<p><strong>Size:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>'
    LINK_PATTERN = r'<a class="select" href="(http://.+?)">Download</a>'

    WAIT_PATTERN = r'Please wait.*?>(\d+)</span>'


    def get_download_link(self):
        #: stage1: press the "Free Download" button
        data = self.get_post_parameters()
        self.html = self.load(self.pyfile.url, post=data)

        #: stage2: wait some time and press the "Download File" button
        data = self.get_post_parameters()
        wait_time = re.search(self.WAIT_PATTERN, self.html, re.M | re.S).group(1)
        self.log_debug("Hoster told us to wait %s seconds" % wait_time)
        self.wait(wait_time)
        self.html = self.load(self.pyfile.url, post=data)

        #: stage3: get the download link
        return re.search(self.LINK_PATTERN, self.html, re.S).group(1)


getInfo = create_getInfo(NosuploadCom)
