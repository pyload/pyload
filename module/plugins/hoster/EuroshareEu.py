# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class EuroshareEu(SimpleHoster):
    __name__ = "EuroshareEu"
    __type__ = "hoster"
    __version__ = "0.25"

    __pattern__ = r'http://(?:www\.)?euroshare.(eu|sk|cz|hu|pl)/file/.*'

    __description__ = """Euroshare.eu hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_INFO_PATTERN = r'<span style="float: left;"><strong>(?P<N>.+?)</strong> \((?P<S>.+?)\)</span>'
    OFFLINE_PATTERN = ur'<h2>S.bor sa nena.iel</h2>|Požadovaná stránka neexistuje!'

    FREE_URL_PATTERN = r'<a href="(/file/\d+/[^/]*/download/)"><div class="downloadButton"'
    ERR_PARDL_PATTERN = r'<h2>Prebieha s.ahovanie</h2>|<p>Naraz je z jednej IP adresy mo.n. s.ahova. iba jeden s.bor'
    ERR_NOT_LOGGED_IN_PATTERN = r'href="/customer-zone/login/"'

    FILE_URL_REPLACEMENTS = [(r"(http://[^/]*\.)(sk|cz|hu|pl)/", r"\1eu/")]


    def setup(self):
        self.multiDL = self.resumeDownload = self.premium
        self.req.setOption("timeout", 120)

    def handlePremium(self):
        if self.ERR_NOT_LOGGED_IN_PATTERN in self.html:
            self.account.relogin(self.user)
            self.retry(reason="User not logged in")

        self.download(self.pyfile.url.rstrip('/') + "/download/")

        check = self.checkDownload({"login": re.compile(self.ERR_NOT_LOGGED_IN_PATTERN),
                                    "json": re.compile(r'\{"status":"error".*?"message":"(.*?)"')})
        if check == "login" or (check == "json" and self.lastCheck.group(1) == "Access token expired"):
            self.account.relogin(self.user)
            self.retry(reason="Access token expired")
        elif check == "json":
            self.fail(self.lastCheck.group(1))

    def handleFree(self):
        if re.search(self.ERR_PARDL_PATTERN, self.html) is not None:
            self.longWait(5 * 60, 12)

        m = re.search(self.FREE_URL_PATTERN, self.html)
        if m is None:
            self.parseError("Parse error (URL)")
        parsed_url = "http://euroshare.eu%s" % m.group(1)
        self.logDebug("URL", parsed_url)
        self.download(parsed_url, disposition=True)

        check = self.checkDownload({"multi_dl": re.compile(self.ERR_PARDL_PATTERN)})
        if check == "multi_dl":
            self.longWait(5 * 60, 12)


getInfo = create_getInfo(EuroshareEu)
