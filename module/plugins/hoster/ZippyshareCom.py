# -*- coding: utf-8 -*-

import re
import urllib

import BeautifulSoup

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class ZippyshareCom(SimpleHoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __version__ = "0.96"
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
            if ".com/pd/" in self.link:
                self.load(self.link)
                self.link = self.link.replace(".com/pd/", ".com/d/")

        if self.link and pyfile.name == "file.html":
            pyfile.name = urllib.unquote(self.link.split('/')[-1])

    def get_link(self):
        m = re.search(r'\(\'dlbutton\'\)\.href = "(.+?)" \+ \((\d+) % (\d+) \+ (\d+) % (\d+)\) \+ "(.+?)";', self.data)
        if m is not None:
            return 'http://%s%s%s%s' % (self.info['pattern']['HOST'], m.group(1),
                                          int(m.group(2)) % int(m.group(3)) + int(m.group(4)) % int(m.group(5)),
                                          m.group(6))

        else:
            return None
