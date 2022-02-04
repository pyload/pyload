# -*- coding: utf-8 -*-

import re
import urllib.parse
from datetime import timedelta

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..base.simple_downloader import SimpleDownloader


class DepositfilesCom(SimpleDownloader):
    __name__ = "DepositfilesCom"
    __type__ = "downloader"
    __version__ = "0.65"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(depositfiles\.com|dfiles\.(eu|ru))(/\w{1,3})?/files/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Depositfiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("spoob", "spoob@pyload.net"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'<script type="text/javascript">eval\( unescape\(\'(?P<N>.*?)\''
    SIZE_PATTERN = r">File size: <b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</b>"
    OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    NAME_REPLACEMENTS = [
        (r"\%u([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16))),
        (r'.*<b title="(?P<N>.+?)".*', r"\g<N>"),
    ]
    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://depositfiles.com/files/\g<ID>")]

    COOKIES = [("depositfiles.com", "lang_current", "en")]

    WAIT_PATTERN = r'(?:download_waiter_remain">|html_download_api-limit_interval">|>Please wait|>Try in).+'
    ERROR_PATTER = r"File is checked, please try again in a minute"

    LINK_FREE_PATTERN = (
        r'<form id="downloader_file_form" action="(https?://.+?)" method="post"'
    )
    LINK_PREMIUM_PATTERN = r'class="repeat"><a href="(.+?)"'
    LINK_MIRROR_PATTERN = r'class="repeat_mirror"><a href="(.+?)"'

    def handle_free(self, pyfile):
        self.data = self.load(pyfile.url, post={"gateway_result": "1", "asm": "0"})

        self.check_errors()

        m = re.search(r"var fid = '(\w+?)'", self.data)
        if m is None:
            self.log_error(self._("fid pattern not found"))
            self.retry(wait=5)

        fid = m.group(1)
        params = {"fid": fid}
        self.log_debug(f"FID: {fid}")

        captcha_data = self.load("https://depositfiles.com/get_file.php", get=params)

        m = re.search(r"ACPuzzleKey = '(.+?)'", captcha_data)
        if m is not None:
            self.captcha = SolveMedia(pyfile)
            captcha_key = m.group(1)
            params["acpuzzle"] = 1
            params["response"], params["challenge"] = self.captcha.challenge(
                captcha_key
            )

        elif re.search(r"check_recaptcha\('(.+?)'", captcha_data) is not None:
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()

            if captcha_key:
                self.captcha = recaptcha
                response = recaptcha.challenge(captcha_key)
                params["g-recaptcha-response"] = response

        else:
            self.log_error(self._("Captcha pattern not found"))
            self.fail(self._("Captcha pattern not found"))

        self.data = self.load("https://depositfiles.com/get_file.php", get=params)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = urllib.parse.unquote(m.group(1))

    def handle_premium(self, pyfile):
        if '<span class="html_download_api-gold_traffic_limit">' in self.data:
            self.log_warning(self._("Download limit reached"))
            self.retry(25, timedelta(hours=1).total_seconds(), "Download limit reached")

        elif 'onClick="show_gold_offer' in self.data:
            self.account.relogin()
            self.retry()

        else:
            link = re.search(self.LINK_PREMIUM_PATTERN, self.data)
            mirror = re.search(self.LINK_MIRROR_PATTERN, self.data)

            if link:
                self.link = link.group(1)

            elif mirror:
                self.link = mirror.group(1)
