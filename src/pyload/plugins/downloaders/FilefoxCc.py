# -*- coding: utf-8 -*-

import re
import urllib.parse

import pycurl

from ..anticaptchas.HCaptcha import HCaptcha
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.xfs_downloader import XFSDownloader
from ..helpers import parse_html_tag_attr_value


class FilefoxCc(XFSDownloader):
    __name__ = "FilefoxCc"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filefox\.cc/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filefox.cc downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filefox.cc"

    DL_LIMIT_PATTERN = r"Wait [\w ]+? or <a href='//filefox.cc/premium'"
    WAIT_PATTERN = r'<span class="time-remain">(\d+)<'

    INFO_PATTERN = (
        r'<p>(?P<N>.+?)</p>\s*<p class="file-size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>'
    )
    NAME_PATTERN = r"^unmatchable$"
    SIZE_REPLACEMENTS = [("Kb", "KB"), ("Mb", "MB"), ("Gb", "GB")]

    LINK_PATTERN = r'<a class="btn btn-default" href="(https://s\d+.filefox.cc/.+?)"'

    @staticmethod
    def filter_form(tag):
        action = parse_html_tag_attr_value("action", tag)
        return ".js" not in action if action else False

    FORM_PATTERN = filter_form
    FORM_INPUTS_MAP = {"op": re.compile(r"^download")}

    def handle_captcha(self, inputs):
        m = re.search(r'\$\.post\( "/ddl",\s*\{(.+?) \} \);', self.data, re.S)

        if m is not None:
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key:
                self.captcha = recaptcha
                response = recaptcha.challenge(captcha_key)

            else:
                hcaptcha = HCaptcha(self.pyfile)
                captcha_key = hcaptcha.detect_key()
                if captcha_key:
                    self.captcha = hcaptcha
                    response = hcaptcha.challenge(captcha_key)

            if captcha_key:
                captcha_inputs = {}
                for _i in m.group(1).split(","):
                    _k, _v = _i.split(":", 1)
                    _k = _k.strip('\n" ')
                    if _k == "g-recaptcha-response":
                        _v = response

                    captcha_inputs[_k] = _v.strip('" ')

                self.req.http.c.setopt(
                    pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"]
                )

                html = self.load(
                    urllib.parse.urljoin(self.pyfile.url, "/ddl"), post=captcha_inputs
                )

                self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

                if html == "OK":
                    self.captcha.correct()

                else:
                    self.retry_captcha()
