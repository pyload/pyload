# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name__    = "FastshareCz"
    __type__    = "hoster"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fastshare\.cz/\d+/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """FastShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [("#.*", "")]

    COOKIES = [("fastshare.cz", "lang", "en")]

    NAME_PATTERN    = r'<h3 class="section_title">(?P<N>.+?)<'
    SIZE_PATTERN    = r'>Size\s*:</strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>(The file has been deleted|Requested page not found)'

    LINK_FREE_PATTERN    = r'>Enter the code\s*:</em>\s*<span><img src="(.+?)"'
    LINK_PREMIUM_PATTERN = r'(http://\w+\.fastshare\.cz/download\.php\?id=\d+&)'

    SLOT_ERROR   = "> 100% of FREE slots are full"
    CREDIT_ERROR = " credit for "


    def check_errors(self):
        if self.SLOT_ERROR in self.html:
            errmsg = self.info['error'] = _("No free slots")
            self.retry(12, 60, errmsg)

        if self.CREDIT_ERROR in self.html:
            errmsg = self.info['error'] = _("Not enough traffic left")
            self.log_warning(errmsg)
            self.restart(nopremium=True)

        self.info.pop('error', None)


    def handle_free(self, pyfile):
        m = re.search(self.FREE_URL_PATTERN, self.html)
        if m:
            action, captcha_src = m.groups()
        else:
            self.error(_("FREE_URL_PATTERN not found"))

        baseurl = "http://www.fastshare.cz"
        captcha = self.captcha.decrypt(urlparse.urljoin(baseurl, captcha_src))
        self.download(urlparse.urljoin(baseurl, action), post={'code': captcha, 'btn.x': 77, 'btn.y': 18})


    def check_file(self):
        check = self.check_download({
            'paralell-dl'  : re.compile(r"<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)"),
            'wrong captcha': re.compile(r'Download for FREE'),
            'credit'       : re.compile(self.CREDIT_ERROR)
        })

        if check == "paralell-dl":
            self.retry(6, 10 * 60, _("Paralell download"))

        elif check == "wrong captcha":
            self.retry(max_tries=5, reason=_("Wrong captcha"))

        elif check == "credit":
            self.restart(nopremium=True)

        return super(FastshareCz, self).check_file()


getInfo = create_getInfo(FastshareCz)
