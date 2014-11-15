# -*- coding: utf-8 -*-
#
# Test links:
# http://www.fastshare.cz/2141189/random.bin

import re

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name__    = "FastshareCz"
    __type__    = "hoster"
    __version__ = "0.23"

    __pattern__ = r'http://(?:www\.)?fastshare\.cz/\d+/.+'

    __description__ = """FastShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN = r'<h1 class="dwp">(?P<N>[^<]+)</h1>\s*<div class="fileinfo">\s*Size\s*: (?P<S>\d+) (?P<U>[\w^_]+),'
    OFFLINE_PATTERN = r'>(The file has been deleted|Requested page not found)'

    URL_REPLACEMENTS = [("#.*", "")]

    COOKIES = [("fastshare.cz", "lang", "en")]

    FREE_URL_PATTERN = r'action=(/free/.*?)>\s*<img src="([^"]*)"><br'
    PREMIUM_URL_PATTERN = r'(http://data\d+\.fastshare\.cz/download\.php\?id=\d+&)'
    CREDIT_PATTERN = r' credit for '


    def handleFree(self):
        if "> 100% of FREE slots are full" in self.html:
            self.retry(12, 60, _("No free slots"))

        m = re.search(self.FREE_URL_PATTERN, self.html)
        if m:
            action, captcha_src = m.groups()
        else:
            self.error(_("FREE_URL_PATTERN not found"))

        baseurl = "http://www.fastshare.cz"
        captcha = self.decryptCaptcha(urljoin(baseurl, captcha_src))
        self.download(urljoin(baseurl, action), post={"code": captcha, "btn.x": 77, "btn.y": 18})

        check = self.checkDownload({
            'paralell_dl': "<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)",
            'wrong_captcha': "Download for FREE"
        })

        if check == "paralell_dl":
            self.retry(6, 10 * 60, _("Paralell download"))
        elif check == "wrong_captcha":
            self.retry(max_tries=5, reason=_("Wrong captcha"))


    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if "location" in header:
            url = header['location']
        elif self.CREDIT_PATTERN in self.html:
            self.logWarning(_("Not enough traffic left"))
            self.resetAccount()
        else:
            m = re.search(self.PREMIUM_URL_PATTERN, self.html)
            if m:
                url = m.group(1)
            else:
                self.error(_("PREMIUM_URL_PATTERN not found"))

        self.logDebug("PREMIUM URL: " + url)
        self.download(url, disposition=True)

        check = self.checkDownload({"credit": re.compile(self.CREDIT_PATTERN)})
        if check == "credit":
            self.resetAccount()


getInfo = create_getInfo(FastshareCz)
