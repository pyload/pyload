# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class EuroshareEu(SimpleHoster):
    __name__    = "EuroshareEu"
    __type__    = "hoster"
    __version__ = "0.30"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?euroshare\.(eu|sk|cz|hu|pl)/file/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Euroshare.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN    = r'<span style="float: left;"><strong>(?P<N>.+?)</strong> \((?P<S>.+?)\)</span>'
    OFFLINE_PATTERN = ur'<h2>S.bor sa nena.iel</h2>|Požadovaná stránka neexistuje!'

    LINK_FREE_PATTERN = r'<a href="(/file/\d+/[^/]*/download/)"><div class="downloadButton"'

    DL_LIMIT_PATTERN = r'<h2>Prebieha s.ahovanie</h2>|<p>Naraz je z jednej IP adresy mo.n. s.ahova. iba jeden s.bor'
    ERROR_PATTERN    = r'href="/customer-zone/login/"'

    URL_REPLACEMENTS = [(r"(http://[^/]*\.)(sk|cz|hu|pl)/", r"\1eu/")]


    def handle_premium(self, pyfile):
        if self.ERROR_PATTERN in self.html:
            self.account.relogin(self.user)
            self.retry(reason=_("User not logged in"))

        self.link = pyfile.url.rstrip('/') + "/download/"

        check = self.check_download({'login': re.compile(self.ERROR_PATTERN),
                                    'json' : re.compile(r'\{"status":"error".*?"message":"(.*?)"')})

        if check == "login" or (check == "json" and self.last_check.group(1) == "Access token expired"):
            self.account.relogin(self.user)
            self.retry(reason=_("Access token expired"))

        elif check == "json":
            self.fail(self.last_check.group(1))


    def handle_free(self, pyfile):
        if re.search(self.DL_LIMIT_PATTERN, self.html):
            self.wait(5 * 60, 12, _("Download limit reached"))

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = "http://euroshare.eu%s" % m.group(1)


getInfo = create_getInfo(EuroshareEu)
