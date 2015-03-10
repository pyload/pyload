# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class EuroshareEu(SimpleHoster):
    __name__    = "EuroshareEu"
    __type__    = "hoster"
    __version__ = "0.28"

    __pattern__ = r'http://(?:www\.)?euroshare\.(eu|sk|cz|hu|pl)/file/.+'

    __description__ = """Euroshare.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN    = r'<span style="float: left;"><strong>(?P<N>.+?)</strong> \((?P<S>.+?)\)</span>'
    OFFLINE_PATTERN = ur'<h2>S.bor sa nena.iel</h2>|Požadovaná stránka neexistuje!'

    LINK_FREE_PATTERN = r'<a href="(/file/\d+/[^/]*/download/)"><div class="downloadButton"'

    ERR_PARDL_PATTERN         = r'<h2>Prebieha s.ahovanie</h2>|<p>Naraz je z jednej IP adresy mo.n. s.ahova. iba jeden s.bor'
    ERR_NOT_LOGGED_IN_PATTERN = r'href="/customer-zone/login/"'

    URL_REPLACEMENTS = [(r"(http://[^/]*\.)(sk|cz|hu|pl)/", r"\1eu/")]


    def handlePremium(self, pyfile):
        if self.ERR_NOT_LOGGED_IN_PATTERN in self.html:
            self.account.relogin(self.user)
            self.retry(reason=_("User not logged in"))

        self.download(pyfile.url.rstrip('/') + "/download/")

        check = self.checkDownload({"login": re.compile(self.ERR_NOT_LOGGED_IN_PATTERN),
                                    "json" : re.compile(r'\{"status":"error".*?"message":"(.*?)"')})

        if check == "login" or (check == "json" and self.lastCheck.group(1) == "Access token expired"):
            self.account.relogin(self.user)
            self.retry(reason=_("Access token expired"))

        elif check == "json":
            self.fail(self.lastCheck.group(1))


    def handleFree(self, pyfile):
        if re.search(self.ERR_PARDL_PATTERN, self.html) is not None:
            self.longWait(5 * 60, 12)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = "http://euroshare.eu%s" % m.group(1)


    def checkFile(self, rules={}):
        if self.checkDownload({"multi-dl": re.compile(self.ERR_PARDL_PATTERN)})
            self.longWait(5 * 60, 12)

        return super(EuroshareEu, self).checkFile(rules)


getInfo = create_getInfo(EuroshareEu)
