# -*- coding: utf-8 -*-

import re
import urllib

from module.network.HTTPRequest import BadHeader

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class FiregetCom(SimpleHoster):
    __name__ = "FiregetCom"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?fireget\.com/(?P<ID>\w{12})/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Fireget.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r'>You have requested .+?> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'

    WAIT_PATTERN = r'<span id="countdown_str">.+?<span .+?>(\d+)</span>'
    DL_LIMIT_PATTERN = r'>You have to wait (.+?) till next download<'

    OFFLINE_PATTERN = r'File Not Found'
    TEMP_OFFLINE_PATTERN = "Connection limit reached|Server error|You have reached the download limit"

    COOKIES = [("fireget.com", "lang", "english")]

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1
        self.resume_download = True

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form(input_names={'op': re.compile(r'^download')})

        if inputs:
            inputs.pop('method_premium', None)
            self.data = self.load(pyfile.url, post=inputs)
            self.check_errors()

        url, inputs = self.parse_html_form('name="F1"')
        if not inputs:
            self.error("Form F1 not found")

        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            response, challenge = self.captcha.challenge(captcha_key)
            inputs['recaptcha_challenge_field'] = challenge
            inputs['recaptcha_response_field'] = response

        else:
            captcha_code = "".join(chr(int(_x[2:4])) if _x[0:2] == '&#' else _x for _p, _x in
                                   sorted(re.findall(r'<span style=[\'"]position:absolute;padding-left:(\d+)px;.+?[\'"]>(.+?)</span>', self.data),
                                          key=lambda _i: int(_i[0])))

            if captcha_code:
                inputs['code'] = captcha_code

            else:
                self.error("Captcha not found")

        self.download(pyfile.url, post=inputs)

    def check_download(self):
        check = self.scan_download({
            'wrong_captcha': ">Wrong captcha<"
        })

        if check == "wrong_captcha":
            self.captcha.invalid()
            self.retry(msg=_("Wrong captcha code"))
