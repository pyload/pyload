# -*- coding: utf-8 -*-

import json
import re

from pyload.core.network.request_factory import get_url

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class OboomCom(SimpleDownloader):
    __name__ = "OboomCom"
    __type__ = "downloader"
    __version__ = "0.47"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?oboom\.com/(?:#(?:id=|/)?)?(?P<ID>\w{8})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Oboom.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stanley", "stanley.foerster@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    RECAPTCHA_KEY = "6Lc7b0IUAAAAAJ7LJfEl9rYKtcxoqyOpuiCzw0eI"

    #: See https://www.oboom.com/api
    API_URL = "https://%s.oboom.com/1/"

    @classmethod
    def api_request(cls, subdomain, method, args={}):
        return json.loads(get_url(cls.API_URL % subdomain + method, post=args))

    @classmethod
    def api_info(cls, url):
        info = {}

        file_id = re.match(cls.__pattern__, url).group("ID")
        res = cls.api_request("api", "info", {"items": file_id})
        if res[0] == 200:
            item = res[1][0]
            if item["state"] == "online":
                info["status"] = 2
                info["name"] = item["name"]
                info["size"] = item["size"]

            else:
                info["status"] = 1
        else:
            info["status"] = 8
            info["error"] = "Could not retrieve file info. Error %s: %s" % (
                res[0],
                res[1],
            )

        return info

    def setup(self):
        self.chunk_limit = 1
        self.multi_dl = self.resume_download = self.premium

    def get_session_token(self):
        if self.account:
            self.session_token = self.account.info["data"]["session"]

        else:
            res = self.api_request("www", "guestsession")
            if res[0] == 200:
                self.session_token = res[1]

            else:
                self.fail(
                    self._("Could not retrieve token for guest session. Error %s: %s")
                    % (res[0], res[1])
                )

    def handle_captcha(self):
        self.captcha = ReCaptcha(self.pyfile)
        response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

        res = self.api_request(
            "www",
            "dl/ticket",
            {
                "recaptcha_response_field": "",
                "g-recaptcha-response": response,
                "download_id": self.info["pattern"]["ID"],
                "token": self.session_token,
            },
        )

        if res[0] == 200:
            self.download_token = res[1]
            self.download_auth = res[2]
            self.captcha.correct()
            self.wait(30)

        elif res[0] == 403:
            if res[1] == -1:  #: Another download is running
                wait_time = 15 * 60
                reconnect = None

            else:
                wait_time = res[1]
                reconnect = True

            self.wait(wait_time, reconnect=reconnect)

            self.retry()

        elif res[0] == 400:
            if res[1] == "forbidden":
                self.retry(wait=15 * 60, msg=self._("Service unavailable"))

            elif res[1] in ("incorrect-captcha-sol", "captcha-timeout"):
                self.retry_captcha()

            else:
                self.fail(self._("Unknown API Error %s") % res[1])

        else:
            self.fail(self._("Unknown API error, Error %s: %s") % (res[0], res[1]))

    def get_download_ticket(self):
        params = {
            "item": self.info["pattern"]["ID"],
            "http_errors": 0,
            "redirect": False,
        }

        if self.premium:
            params["token"] = self.session_token

        else:
            params.update({"token": self.download_token, "auth": self.download_auth})

        res = self.api_request("api", "dl", params)

        if res[0] == 200:
            self.download_domain = res[1]
            self.download_ticket = res[2]

        elif res[0] == 421:
            self.log_warning(self._("Connection limit exceeded"))
            self.retry(wait=res[2] + 60)

        else:
            self.fail(
                self._("Could not retrieve download ticket. Error %s: %s")
                % (res[0], res[1])
            )

    def handle_free(self, pyfile):
        self.get_session_token()
        if not self.premium:
            self.handle_captcha()
        self.get_download_ticket()
        self.download(
            "http://%s/1/dlh" % self.download_domain,
            get={"ticket": self.download_ticket},
        )

    def handle_premium(self, pyfile):
        self.handle_free(self, pyfile)
