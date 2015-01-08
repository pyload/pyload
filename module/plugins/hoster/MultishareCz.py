# -*- coding: utf-8 -*-

import re

from random import random

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MultishareCz(SimpleHoster):
    __name__    = "MultishareCz"
    __type__    = "hoster"
    __version__ = "0.40"

    __pattern__ = r'http://(?:www\.)?multishare\.cz/stahnout/(?P<ID>\d+)'

    __description__ = """MultiShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    SIZE_REPLACEMENTS = [('&nbsp;', '')]

    CHECK_TRAFFIC = True
    MULTI_HOSTER  = True

    INFO_PATTERN    = ur'(?:<li>Název|Soubor): <strong>(?P<N>[^<]+)</strong><(?:/li><li|br)>Velikost: <strong>(?P<S>[^<]+)</strong>'
    OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'


    def handleFree(self, pyfile):
        self.download("http://www.multishare.cz/html/download_free.php", get={'ID': self.info['pattern']['ID']})


    def handlePremium(self, pyfile):
        self.download("http://www.multishare.cz/html/download_premium.php", get={'ID': self.info['pattern']['ID']})


    def handleMulti(self, pyfile):
        self.html = self.load('http://www.multishare.cz/html/mms_ajax.php', post={"link": pyfile.url}, decode=True)

        self.checkInfo()

        if not self.checkTrafficLeft():
            self.fail(_("Not enough credit left to download file"))

        self.download("http://dl%d.mms.multishare.cz/html/mms_process.php" % round(random() * 10000 * random()),
                      get={'u_ID'  : self.acc_info['u_ID'],
                           'u_hash': self.acc_info['u_hash'],
                           'link'  : pyfile.url},
                      disposition=True)


getInfo = create_getInfo(MultishareCz)
