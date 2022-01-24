# -*- coding: utf-8 -*-

import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class ClicknuploadCc(SimpleDownloader):
    __name__ = "ClicknuploadCc"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?clicknupload\.cc/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Clicknupload.cc downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LINK_PATTERN = r"onClick=\"window.open\('(.+?)'\);"

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r">size</span>\s*<span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>"

    WAIT_PATTERN = r'<span class="seconds">(\d+)</span>'

    OFFLINE_PATTERN = r"File Not Found"
    ERROR_PATTERN = ""

    COOKIES = [("clicknupload.cc", "lang", "english")]

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form(input_names={"op": re.compile(r"^download")})

        if inputs:
            inputs.pop("method_premium", None)
            self.data = self.load(pyfile.url, post=inputs)
            self.check_errors()

        url, inputs = self.parse_html_form('name="F1"')
        if not inputs:
            self.error("Form F1 not found")

        self.captcha = ReCaptcha(pyfile)
        captcha_key = self.captcha.detect_key()

        if captcha_key:
            response = self.captcha.challenge(captcha_key)
            inputs["g-recaptcha-response"] = response

        else:
            captcha_code = "".join(
                chr(int(_x[2:4])) if _x[0:2] == "&#" else _x
                for _p, _x in sorted(
                    re.findall(
                        r'<span style=[\'"]position:absolute;padding-left:(\d+)px;.+?[\'"]>(.+?)</span>',
                        self.data,
                    ),
                    key=lambda _i: int(_i[0]),
                )
            )

            if captcha_code:
                inputs["code"] = captcha_code

            else:
                self.error("Captcha not found")

        self.data = self.load(pyfile.url, post=inputs)

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)
