# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class EuroshareEu(SimpleHoster):
    __name__    = "EuroshareEu"
    __type__    = "hoster"
    __version__ = "0.36"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?euroshare\.(eu|sk|cz|hu|pl)/file/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Euroshare.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<h1 class="nazev-souboru">(?P<N>.+?)</h1>'
    SIZE_PATTERN    = r'<p class="posledni vpravo">.*\| (?P<S>.+?) (?P<U>.+?)</p>'

    OFFLINE_PATTERN = ur'<h2>S.bor sa nena.iel</h2>|Požadovaná stránka neexistuje!'

    LINK_FREE_PATTERN = r'onclick="return checkLoad\(\);" href="(.+?)" class="tlacitko velky"'

    DL_LIMIT_PATTERN = r'<h2>Prebieha s.ahovanie</h2>|<p>Naraz je z jednej IP adresy mo.n. s.ahova. iba jeden s.bor'
    ERROR_PATTERN    = r'href="/customer-zone/login/"'

    URL_REPLACEMENTS = [(r"(http://[^/]*\.)(sk|cz|hu|pl)/", r"\1eu/")]


    def handle_premium(self, pyfile):
        if self.ERROR_PATTERN in self.data:
            self.account.relogin()
            self.retry(msg=_("User not logged in"))

        self.link = pyfile.url.rstrip('/') + "/download/"

        check = self.check_file({
            'login': re.compile(self.ERROR_PATTERN),
            'json' : re.compile(r'\{"status":"error".*?"message":"(.*?)"')
        })

        if check == "login" or (check == "json" and self.last_check.group(1) == "Access token expired"):
            self.account.relogin()
            self.retry(msg=_("Access token expired"))

        elif check == "json":
            self.fail(self.last_check.group(1))


    def handle_free(self, pyfile):
        if re.search(self.DL_LIMIT_PATTERN, self.data):
            self.wait(5 * 60, 12, _("Download limit reached"))

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)


getInfo = create_getInfo(EuroshareEu)
