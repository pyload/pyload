# -*- coding: utf-8 -*-

import re
from urlparse import urljoin

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class MultiUpOrg(SimpleCrypter):
    __name    = "MultiUpOrg"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?multiup\.org/(en|fr)/(?P<TYPE>project|download|miror)/\w+(/\w+)?'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """MultiUp.org decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<title>.*(?:Project|Projet|ownload|élécharger) (?P<N>.+?) (\(|- )'


    def getLinks(self):
        m_type = re.match(self.__pattern, self.pyfile.url).group('TYPE')

        if m_type == "project":
            pattern = r'\n(http://www\.multiup\.org/(?:en|fr)/download/.*)'
        else:
            pattern = r'style="width:97%;text-align:left".*\n.*href="(.*)"'
            if m_type == "download":
                dl_pattern = r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>'
                miror_page = urljoin("http://www.multiup.org", re.search(dl_pattern, self.html).group(1))
                self.html = self.load(miror_page)

        return re.findall(pattern, self.html)
