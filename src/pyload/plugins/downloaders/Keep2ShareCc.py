# -*- coding: utf-8 -*-

import json
import random
import re
from datetime import datetime, timedelta, timezone
from enum import Enum

from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_downloader import SimpleDownloader


class Keep2ShareCc(SimpleDownloader):
    __name__ = "Keep2ShareCc"
    __type__ = "downloader"
    __version__ = "0.48"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(keep2share|k2s|keep2s)\.cc/file/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Keep2Share.cc downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
        ("zep6yr", "Ievu6hah[AT]protonmail[DOT]com"),
    ]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://k2s.cc/file/\g<ID>")]

    API_URL = "https://keep2share.cc/api/v2/"
    #: See https://keep2share.github.io/api/ https://github.com/keep2share/api

    class ErrorCode(Enum):
        FILE_IS_NOT_AVAILABLE = 21  # also used for: Traffic limit exceed
        CAPTCHA_REQUIRED = 30
        CAPTCHA_INVALID = 31
        DOWNLOAD_NOT_AVAILABLE = 42

    def api_request(self, method, **kwargs):
        html = self.load(self.API_URL + method, post=json.dumps(kwargs))
        return json.loads(html)

    def api_info(self, url):
        file_id = re.match(self.__pattern__, url).group("ID")
        file_info = self.api_request("GetFilesInfo", ids=[file_id], extended_info=False)

        if (
            file_info["code"] != 200
            or len(file_info["files"]) == 0
            or not file_info["files"][0].get("is_available")
        ):
            return {"status": 1}

        else:
            return {
                "name": file_info["files"][0]["name"],
                "size": file_info["files"][0]["size"],
                "md5": file_info["files"][0]["md5"],
                "access": file_info["files"][0]["access"],
                "free_access": file_info["files"][0]["isAvailableForFree"],
                "status": 2 if file_info["files"][0]["is_available"] else 1,
            }

    def setup(self):
        self.multi_dl = self.premium
        self.resume_download = True

    @staticmethod
    def seconds_until_midnight_utc():
        """calculate seconds until UTC 0:00 and add some randomness"""
        now_utc = datetime.now(timezone.utc)
        midnight_utc = datetime.now(timezone.utc).replace(
            hour=random.randint(0, 2),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )  # prevent clients from retrying all at the same time
        midnight_utc += timedelta(days=1)
        return (midnight_utc - now_utc).total_seconds()

    def solve_captcha(self, req):
        json_data = self.api_request("RequestCaptcha")
        if json_data.get("code") != 200:
            return False
        captcha_response = self.captcha.decrypt(json_data["captcha_url"])
        req["captcha_challenge"] = json_data["challenge"]
        req["captcha_response"] = captcha_response
        return True

    def check_errors(self, data=None):
        if data is not None:
            json_data = json.loads(data)
            if json_data.get("errorCode"):
                err = Keep2ShareCc.ErrorCode(json_data["errorCode"])
                self.log_debug(self._("Handling error code: {}").format(err))

                if err in [err.CAPTCHA_REQUIRED, err.CAPTCHA_INVALID]:
                    self.retry_captcha()

                elif err == err.DOWNLOAD_NOT_AVAILABLE:
                    self.retry(wait=json_data["errors"][0]["timeRemaining"])

                elif err == err.FILE_IS_NOT_AVAILABLE:
                    # apparently traffic will reset at 0:00 UTC
                    self.retry(wait=Keep2ShareCc.seconds_until_midnight_utc())

                else:
                    self.fail(json_data["message"])

    def handle_free(self, pyfile):
        self.do_download(pyfile)

    def handle_premium(self, pyfile):
        self.do_download(pyfile)

    def do_download(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        req = {
            "file_id": file_id,
            "free_download_key": None,
            "captcha_challenge": None,
            "captcha_response": None,
        }

        if self.info["access"] == "private":
            self.fail(self._("This is a private file"))
        elif self.premium:
            req["auth_token"] = self.account.info["data"]["token"]
        elif self.info["access"] == "premium" or self.info["free_access"] is False:
            self.fail(self._("File can be downloaded by premium users only"))

        if not self.premium:
            if not self.solve_captcha(req):
                self.fail(self._("Request captcha API failed"))

        try:
            # The first request will return with "free_download_key"
            # The second request will return with "url"
            for _ in range(2):
                json_data = self.api_request("GetUrl", **req)

                if json_data.get("code") == 200:
                    if req.get("captcha_response", None) is not None:
                        self.captcha.correct()
                        req["captcha_challenge"] = None
                        req["captcha_response"] = None

                    if "url" in json_data:
                        self.link = json_data["url"]
                        break

                    if "free_download_key" in json_data:
                        req["free_download_key"] = json_data["free_download_key"]

                    if "time_wait" in json_data:
                        self.wait(json_data["time_wait"])
                else:
                    self.fail(json_data["message"])

        except BadHeader as exc:
            if exc.code == 406:
                self.check_errors(exc.content)
            else:
                raise
