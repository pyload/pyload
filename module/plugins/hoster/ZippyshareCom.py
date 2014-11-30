# -*- coding: utf-8 -*-

import re

from os.path import join
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__    = "ZippyshareCom"
    __type__    = "hoster"
    __version__ = "0.61"

    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare\.com)/v(?:/|iew\.jsp.*key=)(?P<KEY>\d+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'("\d{6,}/"[ ]*\+.+?"/|<title>Zippyshare.com - )(?P<N>.+?)("|</title>)'
    SIZE_PATTERN = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>File does not exist on this server<'

    COOKIES = [("zippyshare.com", "ziplocale", "en")]


    def setup(self):
        self.multiDL = True
        self.chunkLimit = -1
        self.resumeDownload = True


    def handleFree(self):
        url = self.get_link()
        self.download(url)


    def get_checksum(self):
        try:
            m = re.search(r'\+[ ]*\((\d+)[ ]*\%[ ]*(\d+)[ ]*\+[ ]*(\d+)[ ]*\%[ ]*(\d+)\)[ ]*\+', self.html)
            if m:
                a1, a2, c1, c2 = map(int, m.groups())
            else:
                a1, a2 = map(int, re.search(r'\(\'downloadB\'\).omg = (\d+)%(\d+)', self.html).groups())
                c1, c2 = map(int, re.search(r'\(\'downloadB\'\).omg\) \* \((\d+)%(\d+)', self.html).groups())

            b = (a1 % a2) * (c1 % c2)
        except:
            self.error(_("Unable to calculate checksum"))
        else:
            return b + 18


    def get_link(self):
        checksum = self.get_checksum()
        p_url    = join("d", self.info['KEY'], str(checksum), self.pyfile.name)
        dl_link  = urljoin(self.info['HOST'], p_url)
        return dl_link


getInfo = create_getInfo(ZippyshareCom)
