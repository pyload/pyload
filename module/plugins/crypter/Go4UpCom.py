# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class Go4UpCom(SimpleCrypter):
    __name__    = "Go4UpCom"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://go4up\.com/(dl/\w{12}|rd/\w{12}/\d+)'

    __description__ = """Go4Up.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("rlindner81", "rlindner81@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'(http://go4up\.com/rd/.+?)<'

    NAME_PATTERN = r'<title>Download (.+?)<'

    OFFLINE_PATTERN = r'>\s*(404 Page Not Found|File not Found|Mirror does not exist)'


    def getLinks(self
        links = []

        m = re.search(r'(/download/gethosts/.+?)"')
        if m:
            self.html = self.load(urljoin("http://go4up.com/", m.group(1)))
            pages = [self.load(url) for url in re.findall(self.LINK_PATTERN, self.html)]
        else:
            pages = [self.html]

        for html in pages:
            try:
                links.append(re.search(r'<b><a href="(.+?)"', html).group(1))
            except:
                continue

        return links


getInfo = create_getInfo(Go4UpCom)
