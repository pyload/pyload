# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class RockfileEu(SimpleHoster):
    __name__ = "RockfileEu"
    __type__ = "hoster"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?rockfile\.eu/\w{12}.html'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Rockfile.eu hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r'var iniFileSize = (\d+)'

    WAIT_PATTERN = r'<span id="countdown_str".+?>(\d+)</span>'
    DL_LIMIT_PATTERN = r'You have to wait (?:<b>)?(.+?)(?:</b>)? until you can start another download'

    TEMP_OFFLINE_PATTERN = "Connection limit reached|Server error"

    LINK_FREE_PATTERN = r'href="(http://.+?\.rfservers\.eu.+?)"'

    COOKIES = [("rockfile.eu", "lang", "english")]

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1
        self.resume_download = True

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form("action=''")

        if not inputs:
            self.error("Free download form not found")

        self.data = self.load(pyfile.url, post=inputs)

        for _i in range(5):
            self.check_errors()

            url, inputs = self.parse_html_form('name="F1"')
            if not inputs:
                self.error("Form F1 not found")

            captcha_code = "".join(chr(int(_x[2:4])) if _x[0:2] == '&#' else _x for _p, _x in
                                   sorted(re.findall(r'<span style=[\'"]color:#5d5d5d; text-shadow: 1px 1px #f2f2f2;.+?padding-left:(\d+)px;.+?[\'"]>(.+?)</span>', self.data),
                                          key=lambda _i: int(_i[0])))

            if not captcha_code:
                self.error("Captcha not found")

            captcha_code = captcha_code[1:] if captcha_code[
                0] == '0' else captcha_code  #: Remove leading zero
            captcha_code = captcha_code[1:] if captcha_code[
                0] == '0' else captcha_code  #: Remove leading zero

            inputs['code'] = captcha_code

            self.data = self.load(pyfile.url, post=inputs)

            if r'>Wrong captcha<' in self.data:
                self.log_warning(_("Invalid captcha"), captcha_code)

            else:
                break

        else:
            self.fail(_("Max captcha retries reached"))

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
