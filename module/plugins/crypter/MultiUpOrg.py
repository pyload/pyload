# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MultiUpOrg(SimpleCrypter):
    __name__    = "MultiUpOrg"
    __type__    = "crypter"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?multiup\.org/(en|fr)/(?P<TYPE>project|download|mirror)/\w+(/\w+)?'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

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
                mirror_page = urlparse.urljoin("http://www.multiup.org/", re.search(dl_pattern, self.data).group(1))
                self.data = self.load(mirror_page)

        return re.findall(pattern, self.data)
