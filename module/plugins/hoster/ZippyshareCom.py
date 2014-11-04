# -*- coding: utf-8 -*-

import re

from os import path
from urllib import unquote
from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__    = "ZippyshareCom"
    __type__    = "hoster"
    __version__ = "0.57"

    __pattern__ = r'(?P<HOST>http://www\d{0,2}\.zippyshare\.com)/v(?:/|iew\.jsp.*key=)(?P<KEY>\d+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'var linkz =.*/(?P<N>.+)";'
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


    def getFileInfo(self):
        info = super(ZippyshareCom, self).getFileInfo()
        self.pyfile.name = info['name'] = unquote(info['name'])
        return info


    def get_checksum(self):
        try:
            a = int(re.search(r'var a = (\d+)', self.html).group(1))
            b = int(re.search(r'var ab = a\%(\d+)', self.html).group(1))
        except:
            self.error(_("Unable to calculate checksum"))
        else:
            return a % b


    def get_link(self):
        checksum = self.get_checksum()
        p_url = path.join("d", self.info['KEY'], str(checksum), self.pyfile.name)
        dl_link = urljoin(self.info['HOST'], p_url)
        return dl_link


getInfo = create_getInfo(ZippyshareCom)
