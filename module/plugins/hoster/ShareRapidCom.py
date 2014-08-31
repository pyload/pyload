# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from module.network.RequestFactory import getRequest
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    h = getRequest()
    h.c.setopt(HTTPHEADER,
               ["Accept: text/html",
                "User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"])
    for url in urls:
        html = h.load(url, decode=True)
        file_info = parseFileInfo(ShareRapidCom, url, html)
        yield file_info


class ShareRapidCom(SimpleHoster):
    __name__ = "ShareRapidCom"
    __type__ = "hoster"
    __version__ = "0.54"

    __pattern__ = r'http://(?:www\.)?(share|mega)rapid\.cz/soubor/\d+/.+'

    __description__ = """MegaRapid.cz hoster plugin"""
    __author_name__ = ("MikyWoW", "zoidberg", "stickell", "Walter Purcaro")
    __author_mail__ = ("mikywow@seznam.cz", "zoidberg@mujmail.cz", "l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_NAME_PATTERN = r'<h1[^>]*><span[^>]*>(?:<a[^>]*>)?(?P<N>[^<]+)'
    FILE_SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong></td>'
    OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    SH_CHECK_TRAFFIC = True

    LINK_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'
    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'


    def setup(self):
        self.chunkLimit = 1

    def handlePremium(self):
        try:
            self.html = self.load(self.pyfile.url, decode=True)
        except BadHeader, e:
            self.account.relogin(self.user)
            self.retry(max_tries=3, reason=str(e))

        m = re.search(self.LINK_PATTERN, self.html)
        if m:
            link = m.group(1)
            self.logDebug("Premium link: %s" % link)
            self.download(link, disposition=True)
        else:
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin(self.user)
                self.retry(max_tries=3, reason="User login failed")
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail("Not enough credit left")
            else:
                self.fail("Download link not found")
