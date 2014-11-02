# -*- coding: utf-8 -*-

import re

from os import path
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__    = "ZippyshareCom"
    __type__    = "hoster"
    __version__ = "0.55"

    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare\.com)/v(?:/|iew\.jsp.*key=)(?P<KEY>\d+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<title>Zippyshare.com - (?P<N>.+)</title>'
    SIZE_PATTERN = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>File does not exist on this server<'

    COOKIES = [(".zippyshare.com", "ziplocale", "en")]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = -1
        self.resumeDownload = True


    def handleFree(self):
        url = self.get_link()
        self.download(url)


    def get_checksum(self):
        m = re.search(r'var ab? = (\d+)\%(\d+)', self.html)
        if m:
            return int(m.group(1)) % int(m.group(2))
        else:
            self.error(_("Unable to calculate checksum"))


    def get_link(self):
        checksum = self.get_checksum()
        p_url = path.join("d", self.file_info['KEY'], str(checksum), self.pyfile.name)
        dl_link = urljoin(self.file_info['HOST'], p_url)
        return dl_link


getInfo = create_getInfo(ZippyshareCom)
