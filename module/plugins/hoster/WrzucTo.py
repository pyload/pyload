# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WrzucTo(SimpleHoster):
    __name__ = "WrzucTo"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?wrzuc\.to/([a-zA-Z0-9]+(\.wt|\.html)|(\w+/?linki/[a-zA-Z0-9]+))'

    __description__ = """Wrzuc.to hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'id="file_info">\s*<strong>(?P<N>.*?)</strong>'
    FILE_SIZE_PATTERN = r'class="info">\s*<tr>\s*<td>(?P<S>.*?)</td>'

    SH_COOKIES = [(".wrzuc.to", "language", "en")]


    def setup(self):
        self.multiDL = True

    def handleFree(self):
        data = dict(re.findall(r'(md5|file): "(.*?)"', self.html))
        if len(data) != 2:
            self.parseError('File ID')

        self.req.http.c.setopt(HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.req.http.lastURL = self.pyfile.url
        self.load("http://www.wrzuc.to/ajax/server/prepair", post={"md5": data['md5']})

        self.req.http.lastURL = self.pyfile.url
        self.html = self.load("http://www.wrzuc.to/ajax/server/download_link", post={"file": data['file']})

        data.update(re.findall(r'"(download_link|server_id)":"(.*?)"', self.html))
        if len(data) != 4:
            self.parseError('Download URL')

        download_url = "http://%s.wrzuc.to/pobierz/%s" % (data['server_id'], data['download_link'])
        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)


getInfo = create_getInfo(WrzucTo)
