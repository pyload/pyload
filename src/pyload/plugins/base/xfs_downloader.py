# -*- coding: utf-8 -*-

import re
from datetime import timedelta
from urllib.parse import urljoin

from pyload.core.utils import parse
from pyload.core.utils.web.purge import unescape as html_unescape

from ..anticaptchas.HCaptcha import HCaptcha
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..helpers import search_pattern, set_cookie
from .simple_downloader import SimpleDownloader


class XFSDownloader(SimpleDownloader):
    __name__ = "XFSDownloader"
    __type__ = "downloader"
    __version__ = "0.90"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """XFileSharing downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    PLUGIN_DOMAIN = None
    PLUGIN_URL = None

    DIRECT_LINK = None

    NAME_PATTERN = r'(Filename[ ]*:[ ]*</b>(</td><td nowrap>)?|name="fname"[ ]+value="|<[\w^_]+ class="(file)?name">)\s*(?P<N>.+?)(\s*<|")'
    SIZE_PATTERN = r'(Size[ ]*:[ ]*</b>(</td><td>)?|File:.*>|</font>\s*\(|<[\w^_]+ class="size">)\s*(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'

    OFFLINE_PATTERN = (
        r">\s*\w+ (Not Found|file (was|has been) removed|no longer available)"
    )
    TEMP_OFFLINE_PATTERN = r">\s*\w+ server (is in )?(maintenance|maintainance)"

    WAIT_PATTERN = (
        r'<span id="countdown_str".*>(\d+)</span>|id="countdown" value=".*?(\d+).*?"'
    )
    PREMIUM_ONLY_PATTERN = r">This file is available for Premium Users only"
    HAPPY_HOUR_PATTERN = r">[Hh]appy hour"
    ERROR_PATTERN = r'(?:class=["\']err["\'].*?>|<[Cc]enter><b>|>Error</td>|>\(ERROR:)(?:\s*<.+?>\s*)*(.+?)(?:["\']|<|\))'

    LINK_LEECH_PATTERN = r"<h2>Download Link</h2>\s*<textarea.*?>(.+?)"

    CAPTCHA_PATTERN = r'(https?://[^"\']+?/captchas?/[^"\']+)'
    CAPTCHA_BLOCK_PATTERN = r">Enter code.*?<div.*?>(.+?)</div>"
    RECAPTCHA_PATTERN = None
    HCAPTCHA_PATTERN = None
    SOLVEMEDIA_PATTERN = None

    FORM_PATTERN = None
    FORM_INPUTS_MAP = None  #: Dict passed as `input_names` to `parse_html_form`

    def setup(self):
        self.chunk_limit = -1 if self.premium else 1
        self.multi_dl = self.premium
        self.resume_download = self.premium

    def _set_xfs_cookie(self):
        cookie = (self.PLUGIN_DOMAIN, "lang", "english")
        if isinstance(self.COOKIES, list) and cookie not in self.COOKIES:
            self.COOKIES.insert(cookie)
        else:
            set_cookie(self.req.cj, *cookie)

    def _prepare(self):
        if not self.PLUGIN_DOMAIN:
            self.fail(self._("Missing PLUGIN DOMAIN"))

        if self.COOKIES:
            self._set_xfs_cookie()

        if not self.LINK_PATTERN:
            domain = self.PLUGIN_DOMAIN.replace(".", r"\.")
            self.LINK_PATTERN = rf'(?:file: "(.+?)"|(https?://(?:www\.)?([^/]*?{domain}|\d+\.\d+\.\d+\.\d+)(\:\d+)?(/d/|(/files)?/\d+/\w+/).+?)["\'<])'

        super(XFSDownloader, self)._prepare()

        if self.DIRECT_LINK is None:
            self.direct_dl = self.premium

    def handle_free(self, pyfile):
        for i in range(1, 6):
            self.log_debug(f"Getting download link #{i}...")

            self.check_errors()

            m = search_pattern(self.LINK_PATTERN, self.data, flags=re.S)
            if m is not None:
                self.link = m.group(1)
                break

            self.data = self.load(
                self.PLUGIN_URL or pyfile.url,
                post=self._post_parameters(),
                ref=self.PLUGIN_URL or pyfile.url,
                redirect=False
            )

            if "op=" not in self.last_header.get("location", "op="):
                self.link = self.last_header.get("location")
                break

            m = search_pattern(self.LINK_PATTERN, self.data, flags=re.S)
            if m is not None:
                self.link = m.group(1)
                break
        else:
            self.error(self._("Too many OPs"))

    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)

    def _post_parameters(self):
        if self.FORM_PATTERN or self.FORM_INPUTS_MAP:
            action, inputs = self.parse_html_form(
                self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {}
            )
        else:
            action, inputs = self.parse_html_form(
                input_names={"op": re.compile(r"^download")}
            )

        if not inputs:
            action, inputs = self.parse_html_form("F1")
            if not inputs:
                self.retry(
                    msg=self.info.get("error") or self._("TEXTAREA F1 not found")
                )

        self.log_debug(inputs)

        if "op" in inputs:
            if "password" in inputs:
                password = self.get_password()
                if password:
                    inputs["password"] = password
                else:
                    self.fail(self._("Missing password"))

            if not self.premium:
                m = search_pattern(self.WAIT_PATTERN, self.data)
                if m is not None:
                    try:
                        waitmsg = m.group(1).strip()

                    except (AttributeError, IndexError):
                        waitmsg = m.group(0).strip()

                    wait_time = parse.seconds(waitmsg)
                    self.set_wait(wait_time)
                    if (
                        wait_time
                        < timedelta(minutes=self.config.get("max_wait", 10)).total_seconds()
                        or not self.pyload.config.get("reconnect", "enabled")
                        or not self.pyload.api.is_time_reconnect()
                    ):
                        self.handle_captcha(inputs)

                    self.wait()

                else:
                    self.handle_captcha(inputs)

                if "referer" in inputs and len(inputs["referer"]) == 0:
                    inputs["referer"] = self.PLUGIN_URL or self.pyfile.url

        else:
            inputs["referer"] = self.PLUGIN_URL or self.pyfile.url

        if self.premium:
            inputs["method_premium"] = "Premium Download"
            inputs.pop("method_free", None)
        else:
            inputs["method_free"] = "Free Download"
            inputs.pop("method_premium", None)

        return inputs

    def handle_captcha(self, inputs):
        m = search_pattern(self.CAPTCHA_PATTERN, self.data)
        if m is not None:
            captcha_url = urljoin(self.pyfile.url, m.group(1))
            inputs["code"] = self.captcha.decrypt(captcha_url)
            return

        m = search_pattern(self.CAPTCHA_BLOCK_PATTERN, self.data, flags=re.S)
        if m is not None:
            captcha_div = m.group(1)
            numerals = re.findall(
                r"<span.*?padding-left\s*:\s*(\d+).*?>(\d)</span>",
                html_unescape(captcha_div),
            )

            self.log_debug(captcha_div)

            code = inputs["code"] = "".join(
                a[1] for a in sorted(numerals, key=lambda i: int(i[0]))
            )

            self.log_debug(f"Captcha code: {code}", numerals)
            return

        recaptcha = ReCaptcha(self.pyfile)
        try:
            captcha_key = search_pattern(self.RECAPTCHA_PATTERN, self.data).group(1)

        except (AttributeError, IndexError):
            captcha_key = recaptcha.detect_key()

        else:
            self.log_debug(f"ReCaptcha key: {captcha_key}")

        if captcha_key:
            self.captcha = recaptcha
            inputs["g-recaptcha-response"] = recaptcha.challenge(captcha_key)
            return

        hcaptcha = HCaptcha(self.pyfile)
        try:
            captcha_key = search_pattern(self.HCAPTCHA_PATTERN, self.data).group(1)

        except (AttributeError, IndexError):
            captcha_key = hcaptcha.detect_key()

        else:
            self.log_debug(f"HCaptcha key: {captcha_key}")

        if captcha_key:
            self.captcha = hcaptcha
            inputs["g-recaptcha-response"] = inputs["h-captcha-response"] = hcaptcha.challenge(captcha_key)
            return

        solvemedia = SolveMedia(self.pyfile)
        try:
            captcha_key = search_pattern(self.SOLVEMEDIA_PATTERN, self.data).group(1)

        except (AttributeError, IndexError):
            captcha_key = solvemedia.detect_key()

        else:
            self.log_debug(f"SolveMedia key: {captcha_key}")

        if captcha_key:
            self.captcha = solvemedia
            (
                inputs["adcopy_response"],
                inputs["adcopy_challenge"],
            ) = solvemedia.challenge(captcha_key)
