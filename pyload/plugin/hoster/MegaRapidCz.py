# -*- coding: utf-8 -*-

import re

from pycurl import HTTPHEADER

from pyload.network.HTTPRequest import BadHeader
from pyload.network.RequestFactory import getRequest
from pyload.plugin.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    h = getRequest()
    h.c.setopt(HTTPHEADER,
               ["Accept: text/html",
                "User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"])

    for url in urls:
        html = h.load(url, decode=True)
        yield parseFileInfo(MegaRapidCz, url, html)


class MegaRapidCz(SimpleHoster):
    __name    = "MegaRapidCz"
    __type    = "hoster"
    __version = "0.56"

    __pattern = r'http://(?:www\.)?(share|mega)rapid\.cz/soubor/\d+/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """MegaRapid.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("MikyWoW", "mikywow@seznam.cz"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<h1[^>]*><span[^>]*>(?:<a[^>]*>)?(?P<N>[^<]+)'
    SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong></td>'
    OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    CHECK_TRAFFIC = True

    LINK_PREMIUM_PATTERN = r'<a href="([^"]+)" title="Stahnout">([^<]+)</a>'

    ERR_LOGIN_PATTERN  = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'


    def setup(self):
        self.chunkLimit = 1


    def handlePremium(self, pyfile):
        m = re.search(self.LINK_PREMIUM_PATTERN, self.html)
        if m:
            self.link = m.group(1)
        else:
            if re.search(self.ERR_LOGIN_PATTERN, self.html):
                self.relogin(self.user)
                self.retry(wait_time=60, reason=_("User login failed"))
            elif re.search(self.ERR_CREDIT_PATTERN, self.html):
                self.fail(_("Not enough credit left"))
            else:
                self.fail(_("Download link not found"))
