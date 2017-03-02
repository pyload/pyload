# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class MegaRapidCz(SimpleHoster):
    __name__ = "MegaRapidCz"
    __type__ = "hoster"
    __version__ = "0.64"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?(share|mega)rapid\.cz/soubor/\d+/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """MegaRapid.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("MikyWoW", "mikywow@seznam.cz"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r'<h1.*?><span.*?>(?:<a.*?>)?(?P<N>.+?)'
    SIZE_PATTERN = r'<td class="i">Velikost:</td>\s*<td class="h"><strong>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong></td>'
    OFFLINE_PATTERN = ur'Nastala chyba 404|Soubor byl smazán'

    CHECK_TRAFFIC = True

    LINK_PREMIUM_PATTERN = r'<a href="(.+?)" title="Stahnout">(.+?)</a>'

    ERR_LOGIN_PATTERN = ur'<div class="error_div"><strong>Stahování je přístupné pouze přihlášeným uživatelům'
    ERR_CREDIT_PATTERN = ur'<div class="error_div"><strong>Stahování zdarma je možné jen přes náš'

    def setup(self):
        self.chunk_limit = 1

    def handle_premium(self, pyfile):
        m = re.search(self.LINK_PREMIUM_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

        elif re.search(self.ERR_LOGIN_PATTERN, self.data):
            self.account.relogin()
            self.retry(wait=60, msg=_("User login failed"))

        elif re.search(self.ERR_CREDIT_PATTERN, self.data):
            self.fail(_("Not enough credit left"))
