# -*- coding: utf-8 -*-

import re
import urllib

import BeautifulSoup

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __version__ = "0.95"
    __status__ = "testing"

    __pattern__ = r'https?://(?P<HOST>www\d{0,3}\.zippyshare\.com)/(?:[vd]/|view\.jsp.*key=)(?P<KEY>[\w^_]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Zippyshare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("sebdelsol", "seb.morin@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    COOKIES = [("zippyshare.com", "ziplocale", "en")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://\g<HOST>/v/\g<KEY>/file.html')]

    NAME_PATTERN = r'(?:<title>Zippyshare.com - |"/)(?P<N>[^/]+)(?:</title>|";)'
    SIZE_PATTERN = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'does not exist (anymore )?on this server<'
    TEMP_OFFLINE_PATTERN = r'^unmatchable$'

    LINK_PATTERN = r"document.location = '(.+?)'"

    def setup(self):
        self.chunk_limit = -1
        self.multiDL = True
        self.resume_download = True

    def handle_free(self, pyfile):
        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            try:
                self.link = re.search(self.LINK_PATTERN, self.data)
                self.captcha.challenge()

            except Exception, e:
                self.error(e)

        else:
            self.link = self.get_link()
        if self.link and pyfile.name == "file.html":
            pyfile.name = urllib.unquote(self.link.split('/')[-1])
    def get_link(self):
        reg = r"\(\'dlbutton\'\)\.href = (.+);"
        m = re.search(reg, self.data)
        m = ''.join(chr for chr in m.group(1) if chr not in ['"','(',')','+','%']).replace('  ',' ').split(' ')
        return 'http://{}/d/{}/{}/{}'.format(self.info['pattern']['HOST'], self.info['pattern']['KEY'],
                                             int(m[1]) % int(m[2]) + int(m[3]) % int(m[4]), self.info['pattern']['N'])

