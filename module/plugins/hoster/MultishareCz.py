# -*- coding: utf-8 -*-

import re

from random import random

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MultishareCz(SimpleHoster):
    __name__    = "MultishareCz"
    __type__    = "hoster"
    __version__ = "0.36"

    __pattern__ = r'http://(?:www\.)?multishare\.cz/stahnout/(?P<ID>\d+).*'

    __description__ = """MultiShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    SIZE_REPLACEMENTS = [('&nbsp;', '')]

    MULTI_HOSTER = True

    INFO_PATTERN    = ur'(?:<li>Název|Soubor): <strong>(?P<N>[^<]+)</strong><(?:/li><li|br)>Velikost: <strong>(?P<S>[^<]+)</strong>'
    OFFLINE_PATTERN = ur'<h1>Stáhnout soubor</h1><p><strong>Požadovaný soubor neexistuje.</strong></p>'


    def handleFree(self):
        self.download("http://www.multishare.cz/html/download_free.php?ID=%s" % self.info['pattern']['ID'])


    def handlePremium(self):
        if not self.checkCredit():
            self.logWarning(_("Not enough credit left to download file"))
            self.resetAccount()

        self.download("http://www.multishare.cz/html/download_premium.php?ID=%s" % self.info['pattern']['ID'])


    def handleMulti(self):
        self.html = self.load('http://www.multishare.cz/html/mms_ajax.php', post={"link": self.pyfile.url}, decode=True)

        self.checkInfo()

        if not self.checkCredit():
            self.fail(_("Not enough credit left to download file"))

        url    = "http://dl%d.mms.multishare.cz/html/mms_process.php" % round(random() * 10000 * random())
        params = {"u_ID": self.acc_info['u_ID'], "u_hash": self.acc_info['u_hash'], "link": self.pyfile.url}

        self.logDebug(url, params)

        self.link = True
        self.download(url, get=params)


    def checkCredit(self):
        self.acc_info = self.account.getAccountInfo(self.user, True)

        self.logInfo(_("User %s has %i MB left") % (self.user, self.acc_info['trafficleft'] / 1024))

        return self.pyfile.size / 1024 <= self.acc_info['trafficleft']


getInfo = create_getInfo(MultishareCz)
