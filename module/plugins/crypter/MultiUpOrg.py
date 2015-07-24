# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class MultiUpOrg(SimpleCrypter):
    __name__    = "MultiUpOrg"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?multiup\.org/(en|fr)/(?P<TYPE>project|download|miror)/\w+(/\w+)?'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """MultiUp.org crypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<title>.*(?:Project|Projet|ownload|élécharger) (?P<N>.+?) (\(|- )'


    def get_links(self):
        m_type = re.match(self.__pattern__, self.pyfile.url).group('TYPE')

        if m_type == "project":
            pattern = r'\n(http://www\.multiup\.org/(?:en|fr)/download/.*)'
        else:
            pattern = r'style="width:97%;text-align:left".*\n.*href="(.*)"'
            if m_type == "download":
                dl_pattern = r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>'
                miror_page = urlparse.urljoin("http://www.multiup.org", re.search(dl_pattern, self.html).group(1))
                self.html = self.load(miror_page)

        return re.findall(pattern, self.html)


getInfo = create_getInfo(MultiUpOrg)
