# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class Go4UpCom(SimpleCrypter):
    __name__    = "Go4UpCom"
    __type__    = "crypter"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'http://go4up\.com/(dl/\w{12}|rd/\w{12}/\d+)'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Go4Up.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("rlindner81", "rlindner81@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'(http://go4up\.com/rd/.+?)<'

    NAME_PATTERN = r'<title>Download (.+?)<'

    OFFLINE_PATTERN = r'>\s*(404 Page Not Found|File not Found|Mirror does not exist)'


    def get_links(self):
        links = []

        m = re.search(r'(/download/gethosts/.+?)"', self.html)
        if m:
            self.html = self.load(urlparse.urljoin("http://go4up.com/", m.group(1)))
            pages = [self.load(url) for url in re.findall(self.LINK_PATTERN, self.html)]
        else:
            pages = [self.html]

        for html in pages:
            try:
                links.append(re.search(r'<b><a href="(.+?)"', html).group(1))
            except Exception:
                continue

        return links


getInfo = create_getInfo(Go4UpCom)
