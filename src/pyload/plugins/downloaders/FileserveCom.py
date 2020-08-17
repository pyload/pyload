# -*- coding: utf-8 -*-

import json
import re
from datetime import timedelta

from pyload.core.network.request_factory import get_url
from pyload.core.utils import parse, seconds

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.downloader import BaseDownloader


class FileserveCom(BaseDownloader):
    __name__ = "FileserveCom"
    __type__ = "downloader"
    __version__ = "0.71"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?fileserve\.com/file/(?P<ID>[^/]+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Fileserve.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("mkaay", "mkaay@mkaay.de"),
        ("Paul King", None),
        ("zoidberg", "zoidberg@mujmail.cz"),
    ]

    URLS = [
        "http://www.fileserve.com/file/",
        "http://www.fileserve.com/link-checker.php",
        "http://www.fileserve.com/checkReCaptcha.php",
    ]

    CAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey=\'(.+?)\'"
    LONG_WAIT_PATTERN = r'<li class="title">You need to wait (\d+) (\w+) to start another download\.</li>'
    LINK_EXPIRED_PATTERN = r"Your download link has expired"
    DL_LIMIT_PATTERN = r"Your daily download limit has been reached"
    NOT_LOGGED_IN_PATTERN = r'<form (name="loginDialogBoxForm"|id="login_form")|<li><a href="/login\.php">Login</a></li>'

    LINKCHECK_TR = r"<tr>\s*(<td>http://www\.fileserve\.com/file/.*?)</tr>"
    LINKCHECK_TD = r"<td>(?:<.*?>|&nbsp;)*([^<]*)"

    def setup(self):
        self.resume_download = self.multi_dl = self.premium
        self.file_id = re.match(self.__pattern__, self.pyfile.url).group("ID")
        self.url = "{}{}".format(self.URLS[0], self.file_id)

        self.log_debug(f"File ID: {self.file_id} URL: {self.url}")

    def _get_info(self, url):
        html = get_url(self.URLS[1], post={"urls": url})
        file_info = []
        for li in re.finditer(self.LINKCHECK_TR, html, re.S):
            try:
                cols = re.findall(self.LINKCHECK_TD, li.group(1))
                if cols:
                    file_info.append(
                        (
                            cols[1] if cols[1] != "--" else cols[0],
                            parse.bytesize(cols[2]) if cols[2] != "--" else 0,
                            2 if cols[3].startswith("Available") else 1,
                            cols[0],
                        )
                    )
            except Exception:
                continue
        return file_info

    def process(self, pyfile):
        pyfile.name, pyfile.size, status, self.url = self._get_info(self.url)
        if status != 2:
            self.offline()
        self.log_debug(f"File Name: {pyfile.name} Size: {pyfile.size}")

        if self.premium:
            self.handle_premium()
        else:
            self.handle_free()

    def handle_free(self):
        self.data = self.load(self.url)
        action = self.load(self.url, post={"checkDownload": "check"})
        action = json.loads(action)
        self.log_debug(action)

        if "fail" in action:
            if action["fail"] == "timeLimit":
                self.data = self.load(
                    self.url,
                    post={"checkDownload": "showError", "errorType": "timeLimit"},
                )

                self.do_long_wait(re.search(self.LONG_WAIT_PATTERN, self.data))

            elif action["fail"] == "parallelDownload":
                self.log_warning(self._("Parallel download error, now waiting 60s"))
                self.retry(wait=60, msg=self._("parallelDownload"))

            else:
                self.fail(self._("Download check returned: {}").format(action["fail"]))

        elif "success" in action:
            if action["success"] == "showCaptcha":
                self.do_captcha()
                self.do_timmer()
            elif action["success"] == "showTimmer":
                self.do_timmer()

        else:
            self.error(self._("Unknown server response"))

        #: Show download link
        res = self.load(self.url, post={"downloadLink": "show"})
        self.log_debug(f"Show downloadLink response: {res}")
        if "fail" in res:
            self.error(self._("Couldn't retrieve download url"))

        #: This may either download our file or forward us to an error page
        self.download(self.url, post={"download": "normal"})
        self.log_debug(self.req.http.last_effective_url)

        check = self.scan_download(
            {
                "expired": self.LINK_EXPIRED_PATTERN,
                "wait": re.compile(self.LONG_WAIT_PATTERN),
                "limit": self.DL_LIMIT_PATTERN,
            }
        )

        if check == "expired":
            self.log_debug("Download link was expired")
            self.retry()

        elif check == "wait":
            self.do_long_wait(self.last_check)

        elif check == "limit":
            self.log_warning(self._("Download limited reached for today"))
            self.wait(seconds.to_midnight(), True)
            self.retry()

        #: Ease issue with later downloads appearing to be in parallel
        self.thread.m.reconnecting.wait(3)

    def do_timmer(self):
        res = self.load(self.url, post={"downloadLink": "wait"})
        self.log_debug(f"Wait response: {res[:80]}")

        if "fail" in res:
            self.fail(self._("Failed getting wait time"))

        if self.__name__ == "FilejungleCom":
            m = re.search(r'"waitTime":(\d+)', res)
            if m is None:
                self.fail(self._("Cannot get wait time"))
            wait_time = int(m.group(1))
        else:
            wait_time = int(res) + 3

        self.wait(wait_time)

    def do_captcha(self):
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.data).group(1)
        self.captcha = ReCaptcha(self.pyfile)

        response, challenge = self.captcha.challenge(captcha_key)
        html = self.load(
            self.URLS[2],
            post={
                "recaptcha_challenge_field": challenge,
                "recaptcha_response_field": response,
                "recaptcha_shortencode_field": self.file_id,
            },
        )
        res = json.loads(html)
        if res["success"]:
            self.captcha.correct()
        else:
            self.retry_captcha()

    def do_long_wait(self, m):
        wait_time = (
            (int(m.group(1)) * {"seconds": 1, "minutes": 60, "hours": 3600}[m.group(2)])
            if m
            else timedelta(minutes=12).seconds
        )
        self.wait(wait_time, True)
        self.retry()

    def handle_premium(self):
        premium_url = None
        if self.__name__ == "FileserveCom":
            #: Try api download
            res = self.load(
                "http://app.fileserve.com/api/download/premium/",
                post={
                    "username": self.account.user,
                    "password": self.account.get_login("password"),
                    "shorten": self.file_id,
                },
            )
            if res:
                res = json.loads(res)
                if res["error_code"] == "302":
                    premium_url = res["next"]

                elif res["error_code"] in ["305", "500"]:
                    self.temp_offline()

                elif res["error_code"] in ["403", "605"]:
                    self.restart(premium=False)

                elif res["error_code"] in ["606", "607", "608"]:
                    self.offline()

                else:
                    self.log_error(res["error_code"], res["error_message"])

        self.download(premium_url or self.pyfile.url)

        if not premium_url and self.scan_download(
            {"login": re.compile(self.NOT_LOGGED_IN_PATTERN)}
        ):
            self.account.relogin()
            self.retry(msg=self._("Not logged in"))
