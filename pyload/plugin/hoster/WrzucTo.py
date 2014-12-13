# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class WrzucTo(SimpleHoster):
    __name    = "WrzucTo"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?wrzuc\.to/(\w+(\.wt|\.html)|(\w+/?linki/\w+))'

    __description = """Wrzuc.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'id="file_info">\s*<strong>(?P<N>.*?)</strong>'
    SIZE_PATTERN = r'class="info">\s*<tr>\s*<td>(?P<S>.*?)</td>'

    COOKIES = [("wrzuc.to", "language", "en")]


    def setup(self):
        self.multiDL = True


    def handleFree(self):
        data = dict(re.findall(r'(md5|file): "(.*?)"', self.html))
        if len(data) != 2:
            self.error(_("No file ID"))

        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = self.pyfile.url
        self.load("http://www.wrzuc.to/ajax/server/prepair", post={"md5": data['md5']})

        self.req.http.lastURL = self.pyfile.url
        self.html = self.load("http://www.wrzuc.to/ajax/server/download_link", post={"file": data['file']})

        data.update(re.findall(r'"(download_link|server_id)":"(.*?)"', self.html))
        if len(data) != 4:
            self.error(_("No download URL"))

        download_url = "http://%s.wrzuc.to/pobierz/%s" % (data['server_id'], data['download_link'])
        self.download(download_url)


getInfo = create_getInfo(WrzucTo)
