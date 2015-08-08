# -*- coding: utf-8 -*-

import pycurl
import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WrzucTo(SimpleHoster):
    __name__    = "WrzucTo"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?wrzuc\.to/(\w+(\.wt|\.html)|(\w+/?linki/\w+))'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Wrzuc.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'id="file_info">\s*<strong>(?P<N>.*?)</strong>'
    SIZE_PATTERN = r'class="info">\s*<tr>\s*<td>(?P<S>.*?)</td>'

    COOKIES = [("wrzuc.to", "language", "en")]


    def setup(self):
        self.multiDL = True


    def handle_free(self, pyfile):
        data = dict(re.findall(r'(md5|file): "(.*?)"', self.html))
        if len(data) != 2:
            self.error(_("No file ID"))

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = pyfile.url
        self.load("http://www.wrzuc.to/ajax/server/prepair", post={'md5': data['md5']})

        self.req.http.lastURL = pyfile.url
        self.html = self.load("http://www.wrzuc.to/ajax/server/download_link", post={'file': data['file']})

        data.update(re.findall(r'"(download_link|server_id)":"(.*?)"', self.html))
        if len(data) != 4:
            self.error(_("No download URL"))

        self.link = "http://%s.wrzuc.to/pobierz/%s" % (data['server_id'], data['download_link'])


getInfo = create_getInfo(WrzucTo)
