# -*- coding: utf-8 -*-

import json
import re
from datetime import timedelta

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.downloader import BaseDownloader

#
# Test links:
# https://www.oboom.com/B7CYZIEB/10Mio.dat


class OboomCom(BaseDownloader):
    __name__ = "OboomCom"
    __type__ = "downloader"
    __version__ = "0.46"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?oboom\.com/(?:#(?:id=|/)?)?(?P<ID>\w{8})"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Oboom.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stanley", "stanley.foerster@gmail.com")]

    RECAPTCHA_KEY = "6LdqpO0SAAAAAJGHXo63HyalP7H4qlRs_vff0kJX"

    def setup(self):
        self.chunk_limit = 1
        self.multi_dl = self.resume_download = self.premium

    def process(self, pyfile):
        self.pyfile.url.replace(".com/#id=", ".com/#")
        self.pyfile.url.replace(".com/#/", ".com/#")
        self.data = self.load(pyfile.url)
        self.get_file_id(self.pyfile.url)
        self.get_session_token()
        self.get_file_info(self.session_token, self.file_id)
        self.pyfile.name = self.file_name
        self.pyfile.size = self.file_size
        if not self.premium:
            self.solve_captcha()
        self.get_download_ticket()
        self.download(
            f"http://{self.download_domain}/1.0/dlh",
            get={"ticket": self.download_ticket, "http_errors": 0},
        )

    def load_url(self, url, get={}):
        return json.loads(self.load(url, get))

    def get_file_id(self, url):
        self.file_id = re.match(OboomCom.__pattern__, url).group("ID")

    def get_session_token(self):
        if self.premium:
            accountInfo = self.account.get_data()
            if "session" in accountInfo:
                self.session_token = accountInfo["session"]
            else:
                self.fail(self._("Could not retrieve premium session"))
        else:
            apiUrl = "http://www.oboom.com/1.0/guestsession"
            result = self.load_url(apiUrl)
            if result[0] == 200:
                self.session_token = result[1]
            else:
                self.fail(
                    self._(
                        "Could not retrieve token for guest session. Error code: {}"
                    ).format(result[0])
                )

    def solve_captcha(self):
        self.captcha = ReCaptcha(self.pyfile)
        response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

        apiUrl = "http://www.oboom.com/1.0/download/ticket"
        params = {
            "recaptcha_challenge_field": challenge,
            "recaptcha_response_field": response,
            "download_id": self.file_id,
            "token": self.session_token,
        }

        result = self.load_url(apiUrl, params)

        if result[0] == 200:
            self.download_token = result[1]
            self.download_auth = result[2]
            self.captcha.correct()
            self.wait(30)

        elif result[0] == 403:
            if result[1] == -1:  #: Another download is running
                wait_time = timedelta(minutes=15).seconds
                reconnect = None
            else:
                wait_time = result[1]
                reconnect = True

            self.wait(wait_time, reconnect=reconnect)

            self.retry()

        elif result[0] == 400 and result[1] == "forbidden":
            self.retry(5, timedelta(minutes=15).seconds, self._("Service unavailable"))

        else:
            self.retry_captcha()

    def get_file_info(self, token, fileId):
        apiUrl = "http://api.oboom.com/1.0/info"
        params = {"token": token, "items": fileId, "http_errors": 0}

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            item = result[1][0]
            if item["state"] == "online":
                self.file_size = item["size"]
                self.file_name = item["name"]
            else:
                self.offline()
        else:
            self.fail(
                self._("Could not retrieve file info. Error code {}: {}").format(
                    result[0], result[1]
                )
            )

    def get_download_ticket(self):
        apiUrl = "http://api.oboom.com/1/dl"
        params = {"item": self.file_id, "http_errors": 0}
        if self.premium:
            params["token"] = self.session_token
        else:
            params["token"] = self.download_token
            params["auth"] = self.download_auth

        result = self.load_url(apiUrl, params)
        if result[0] == 200:
            self.download_domain = result[1]
            self.download_ticket = result[2]
        elif result[0] == 421:
            self.retry(wait=result[2] + 60, msg=self._("Connection limit exceeded"))
        else:
            self.fail(
                self._("Could not retrieve download ticket. Error code: {}").format(
                    result[0]
                )
            )
