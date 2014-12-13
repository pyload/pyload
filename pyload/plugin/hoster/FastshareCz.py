# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name    = "FastshareCz"
    __type    = "hoster"
    __version = "0.25"

    __pattern = r'http://(?:www\.)?fastshare\.cz/\d+/.+'

    __description = """FastShare.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [("#.*", "")]

    COOKIES = [("fastshare.cz", "lang", "en")]

    INFO_PATTERN    = r'<h1 class="dwp">(?P<N>[^<]+)</h1>\s*<div class="fileinfo">\s*Size\s*: (?P<S>\d+) (?P<U>[\w^_]+),'
    OFFLINE_PATTERN = r'>(The file has been deleted|Requested page not found)'

    LINK_FREE_PATTERN    = r'action=(/free/.*?)>\s*<img src="([^"]*)"><br'
    LINK_PREMIUM_PATTERN = r'(http://data\d+\.fastshare\.cz/download\.php\?id=\d+&)'

    SLOT_ERROR   = "> 100% of FREE slots are full"
    CREDIT_ERROR = " credit for "


    def checkErrors(self):
        if self.SLOT_ERROR in self.html:
            errmsg = self.info['error'] = _("No free slots")
            self.retry(12, 60, errmsg)

        if self.CREDIT_ERROR in self.html:
            errmsg = self.info['error'] = _("Not enough traffic left")
            self.logWarning(errmsg)
            self.resetAccount()

        self.info.pop('error', None)


    def handleFree(self):
        m = re.search(self.FREE_URL_PATTERN, self.html)
        if m:
            action, captcha_src = m.groups()
        else:
            self.error(_("FREE_URL_PATTERN not found"))

        baseurl = "http://www.fastshare.cz"
        captcha = self.decryptCaptcha(urljoin(baseurl, captcha_src))
        self.download(urljoin(baseurl, action), post={'code': captcha, 'btn.x': 77, 'btn.y': 18})


    def checkFile(self):
        check = self.checkDownload({
            'paralell_dl'  : re.compile(r"<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)"),
            'wrong_captcha': re.compile(r'Download for FREE'),
            'credit'       : re.compile(self.CREDIT_ERROR)
        })

        if check == "paralell_dl":
            self.retry(6, 10 * 60, _("Paralell download"))

        elif check == "wrong_captcha":
            self.retry(max_tries=5, reason=_("Wrong captcha"))

        elif check == "credit":
            self.resetAccount()


getInfo = create_getInfo(FastshareCz)
