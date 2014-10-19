# -*- coding: utf-8 -*-

import re

from os import path
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __version__ = "0.53"

    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare\.com)/v(?:/|iew\.jsp.*key=)(?P<KEY>\d+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    FILE_NAME_PATTERN = r'var \w+ = .+ \+ "/(?P<N>.+)";'
    FILE_SIZE_PATTERN = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>File does not exist on this server<'

    COOKIES = [(".zippyshare.com", "ziplocale", "en")]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = -1
        self.resumeDownload = True


    def handleFree(self):
        url = self.get_link()
        self.logDebug("Download URL: %s" % url)
        self.download(url)


    def get_checksum(self):
        m = re.search(r'\(a\*b\+19\)', self.html)
        if m:
            m = re.findall(r'var \w = (\d+)\%(\d+);', self.html)
            c = lambda a,b: a * b + 19
        else:
            m = re.findall(r'(\d+) \% (\d+)', self.html)
            c = lambda a,b: a + b

        if not m:
            self.parseError("Unable to calculate checksum")

        a = map(lambda x: int(x), m[0])
        b = map(lambda x: int(x), m[1])

        # Checksum is calculated as (a*b+19) or (a+b), where a and b are the result of modulo calculations
        a = a[0] % a[1]
        b = b[0] % b[1]

        return c(a, b)


    def get_link(self):
        checksum = self.get_checksum()
        p_url = path.join("d", self.file_info['KEY'], str(checksum), self.pyfile.name)
        dl_link = urljoin(self.file_info['HOST'], p_url)
        return dl_link


getInfo = create_getInfo(ZippyshareCom)
