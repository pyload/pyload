# -*- coding: utf-8 -*-

import random
import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class MultishareCz(SimpleHoster):
    __name__    = "MultishareCz"
    __type__    = "hoster"
    __version__ = "0.46"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?multishare\.cz/stahnout/(?P<ID>\d+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """MultiShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    SIZE_REPLACEMENTS = [('&nbsp;', '')]

    CHECK_TRAFFIC = True
    LEECH_HOSTER  = True

    INFO_PATTERN    = ur'(?:<li>Název|Soubor): <strong>(?P<N>.+?)</strong><(?:/li><li|br)>Velikost: <strong>(?P<S>.+?)</strong>'
    OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'


    def handle_free(self, pyfile):
        self.download("http://www.multishare.cz/html/download_free.php", get={'ID': self.info['pattern']['ID']})


    def handle_premium(self, pyfile):
        self.download("http://www.multishare.cz/html/download_premium.php", get={'ID': self.info['pattern']['ID']})


    def handle_multi(self, pyfile):
        self.data = self.load('http://www.multishare.cz/html/mms_ajax.php', post={'link': pyfile.url})

        self.update_info()

        if self.out_of_traffic():
            self.fail(_("Not enough credit left to download file"))

        self.download("http://dl%d.mms.multishare.cz/html/mms_process.php" % round(random.random() * 10000 * random.random()),
                      get={'u_ID'  : self.acc_info['u_ID'],
                           'u_hash': self.acc_info['u_hash'],
                           'link'  : pyfile.url},
                      disposition=True)
