# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FastshareCz(SimpleHoster):
    __name__    = "FastshareCz"
    __type__    = "hoster"
    __version__ = "0.38"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fastshare\.cz/\d+/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

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
        if self.SLOT_ERROR in self.data:
            errmsg = self.info['error'] = _("No free slots")
            self.retry(12, 60, errmsg)

        if self.CREDIT_ERROR in self.data:
            errmsg = self.info['error'] = _("Not enough traffic left")
            self.log_warning(errmsg)
            self.restart(premium=False)

        self.info.pop('error', None)


    def handle_free(self, pyfile):
        m = re.search(self.FREE_URL_PATTERN, self.data)
        if m is not None:
            action, captcha_src = m.groups()
        else:
            self.error(_("FREE_URL_PATTERN not found"))

        baseurl = "http://www.fastshare.cz"
        captcha = self.captcha.decrypt(urlparse.urljoin(baseurl, captcha_src))
        self.download(urlparse.urljoin(baseurl, action), post={'code': captcha, 'btn.x': 77, 'btn.y': 18})


    def check_download(self):
        check = self.check_file({
            'paralell-dl'  : re.compile(r"<title>FastShare.cz</title>|<script>alert\('Pres FREE muzete stahovat jen jeden soubor najednou.'\)"),
            'wrong captcha': re.compile(r'Download for FREE'),
            'credit'       : re.compile(self.CREDIT_ERROR)
        })

        if check == "paralell-dl":
            self.retry(6, 10 * 60, _("Paralell download"))

        elif check == "wrong captcha":
            self.retry_captcha()

        elif check == "credit":
            self.restart(premium=False)

        return super(FastshareCz, self).check_download()


getInfo = create_getInfo(FastshareCz)
