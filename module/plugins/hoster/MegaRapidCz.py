# -*- coding: utf-8 -*-

import pycurl
import re

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest as get_request
from module.plugins.internal.SimpleHoster import SimpleHoster, parse_fileInfo


def get_info(urls):
    h = get_request()
    h.c.setopt(pycurl.HTTPHEADER,
               ["Accept: text/html",
                "User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/25.0"])

    for url in urls:
        html = h.load(url)
        yield parse_fileInfo(MegaRapidCz, url, html)


class MegaRapidCz(SimpleHoster):
    __name__    = "MegaRapidCz"
    __type__    = "hoster"
    __version__ = "0.57"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(share|mega)rapid\.cz/soubor/\d+/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """MegaRapid.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("MikyWoW", "mikywow@seznam.cz"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<h1.*?><span.*?>(?:<a.*?>)?(?P<N>[^<]+)'
    SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong></td>'
    OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    CHECK_TRAFFIC = True

    LINK_PREMIUM_PATTERN = r'<a href="(.+?)" title="Stahnout">([^<]+)</a>'

    ERR_LOGIN_PATTERN  = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'


    def setup(self):
        self.chunk_limit = 1


    def handle_premium(self, pyfile):
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
