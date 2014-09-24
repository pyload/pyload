# -*- coding: utf-8 -*-

import re

from os import path
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __version__ = "0.50"

    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare.com)/v(?:/|iew.jsp.*key=)(?P<KEY>\d+)'

    __description__ = """ Zippyshare.com hoster plugin """
    __author_name__ = ("stickell", "skylab", "Walter Purcaro")
    __author_mail__ = ("l.stickell@yahoo.it", "development@sky-lab.de", "vuolter@gmail.com")


    FILE_NAME_PATTERN = r'<title>Zippyshare\.com - (?P<N>[^<]+)</title>'
    FILE_SIZE_PATTERN = r'>Size:</font>\s*<font [^>]*>(?P<S>[0-9.,]+) (?P<U>[kKMG]+)i?B</font><br />'
    FILE_INFO_PATTERN = r'document\.getElementById\(\'dlbutton\'\)\.href = "[^;]*/(?P<N>[^"]+)";'
    OFFLINE_PATTERN = r'>File does not exist on this server<'

    SH_COOKIES = [(".zippyshare.com", "ziplocale", "en")]


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True


    def handleFree(self):
        url = self.get_link()
        self.logDebug("Download URL: %s" % url)
        self.download(url)


    def get_checksum(self):
        m_a = re.search(r'var a = (\d+)\%(\d+);', self.html)
        m_b = re.search(r'var b = (\d+)\%(\d+);', self.html)
        if m_a is None or m_b is None:
            self.parseError("Unable to calculate checksum")

        # Checksum is calculated as (a*b+19), where a and b are the result of modulo calculations
        a = map(lambda x: int(x), m_a.groups())
        b = map(lambda x: int(x), m_b.groups())
        return a[0] % a[1] * b[0] % b[1] + 19


    def get_link(self):
        checksum = self.get_checksum()
        p_url = path.join("d", self.file_info['KEY'], str(checksum), self.pyfile.name)
        dl_link = urljoin(self.file_info['HOST'], p_url)
        return dl_link


getInfo = create_getInfo(ZippyshareCom)
