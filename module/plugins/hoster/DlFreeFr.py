#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class DlFreeFr(SimpleHoster):
    __name__ = "DlFreeFr"
    __type__ = "hoster"
    __pattern__ = r"http://dl\.free\.fr/([a-zA-Z0-9]+|getfile\.pl\?file=/[a-zA-Z0-9]+)$"
    __version__ = "0.2"
    __description__ = """dl.free.fr download hoster"""
    __author_name__ = ("the-razer", "zoidberg")
    __author_mail__ = ("daniel_ AT gmx DOT net", "zoidberg@mujmail.cz")
       
    FILE_NAME_PATTERN = r"Fichier:</td>\s*<td[^>]*>(?P<N>[^>]*)</td>"
    FILE_SIZE_PATTERN = r"Taille:</td>\s*<td[^>]*>(?P<S>[\d.]+[KMG])</td>"
    FILE_OFFLINE_PATTERN = r"Erreur 404 - Document non trouv|Fichier inexistant|Le fichier demand&eacute; n'a pas &eacute;t&eacute; trouv&eacute;"
    FILE_URL_PATTERN = r'href="(?P<url>http://.*?)">T&eacute;l&eacute;charger ce fichier'
    
    def setup(self):
        self.multiDL = True
        self.limitDL = 5
        self.resumeDownload = True
        self.chunkLimit = 1

    def handleFree(self):
        if "Trop de slots utilis&eacute;s" in self.html:
            self.retry(300)
        
        m = re.search(self.FILE_URL_PATTERN, self.html)
        if not m: self.parseError('URL')
        
        url = m.group('url')
        self.logDebug("File URL [%s]" % url)
        self.download(url)

getInfo = create_getInfo(DlFreeFr)   