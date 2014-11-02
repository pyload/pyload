# -*- coding: utf-8 -*-

import re
from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MultiUpOrg(SimpleCrypter):
    __name__    = "MultiUpOrg"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?multiup\.org/(en|fr)/(?P<TYPE>project|download|miror)/\w+(/\w+)?'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """MultiUp.org crypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<title>.*(?:Project|Projet|ownload|élécharger) (.+?) (?:\(|- )'


    def getLinks(self):
        m_type = re.match(self.__pattern__, self.pyfile.url).group("TYPE")

        if m_type == "project":
            pattern = r'\n(http://www\.multiup\.org/(?:en|fr)/download/.*)'
        else:
            pattern = r'style="width:97%;text-align:left".*\n.*href="(.*)"'
            if m_type == "download":
                dl_pattern = r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>'
                miror_page = urljoin("http://www.multiup.org", re.search(dl_pattern, self.html).group(1))
                self.html = self.load(miror_page)

        return re.findall(pattern, self.html)
