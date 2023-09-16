# -*- coding: utf-8 -*-

import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_downloader import SimpleDownloader


class FileboomMe(SimpleDownloader):
    __name__ = "FileboomMe"
    __type__ = "downloader"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"https?://f(?:ile)?boom\.me/file/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Fileboom.me downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://fileboom.me/api/v2/"
    #: Actually this is Keep2ShareCc API, see https://keep2share.github.io/api/ https://github.com/keep2share/api

    def api_request(self, method, **kwargs):
        html = self.load(self.API_URL + method, post=json.dumps(kwargs))
        return json.loads(html)

    def api_info(self, url):
        file_id = re.match(self.__pattern__, url).group("ID")
        file_info = self.api_request("GetFilesInfo", ids=[file_id], extended_info=False)

        if (
            file_info["code"] != 200
            or len(file_info["files"]) == 0
            or file_info["files"][0].get("is_available", False) is False
        ):
            return {"status": 1}

        else:
            return {
                "name": file_info["files"][0]["name"],
                "size": file_info["files"][0]["size"],
                "md5": file_info["files"][0]["md5"],
                "access": file_info["files"][0]["access"],
                "status": 2 if file_info["files"][0]["is_available"] else 1,
            }

    def setup(self):
        self.resume_download = True
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        if self.info["access"] == "premium":
            self.fail(self._("File can be downloaded by premium users only"))

        elif self.info["access"] == "private":
            self.fail(self._("This is a private file"))

        try:
            api_data = self.api_request(
                "GetUrl",
                file_id=file_id,
                free_download_key=None,
                captcha_challenge=None,
                captcha_response=None,
            )

        except BadHeader as exc:
            if exc.code == 406:
                for i in range(10):
                    api_data = self.api_request("RequestCaptcha")
                    if api_data["code"] != 200:
                        self.fail(self._("Request captcha API failed"))

                    captcha_response = self.captcha.decrypt(api_data["captcha_url"])
                    try:
                        api_data = self.api_request(
                            "GetUrl",
                            file_id=file_id,
                            free_download_key=None,
                            captcha_challenge=api_data["challenge"],
                            captcha_response=captcha_response,
                        )

                    except BadHeader as exc:
                        if exc.code == 406:
                            api_data = json.loads(exc.content)
                            if api_data["errorCode"] == 31:  #: ERROR_CAPTCHA_INVALID
                                self.captcha.invalid()
                                continue

                            elif (
                                api_data["errorCode"] == 42
                            ):  #: ERROR_DOWNLOAD_NOT_AVAILABLE
                                self.captcha.correct()
                                self.retry(wait=api_data["errors"][0]["timeRemaining"])

                            else:
                                self.fail(api_data["message"])

                        else:
                            raise

                    else:
                        self.captcha.correct()
                        free_download_key = api_data["free_download_key"]
                        break

                else:
                    self.fail(self._("Max captcha retries reached"))

                self.wait(api_data["time_wait"])

                api_data = self.api_request(
                    "GetUrl",
                    file_id=file_id,
                    free_download_key=free_download_key,
                    captcha_challenge=None,
                    captcha_response=None,
                )

                if api_data["code"] == 200:
                    self.download(api_data["url"])

            else:
                raise

        else:
            self.download(api_data["url"])

    def handle_premium(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        if self.info["access"] == "private":
            self.fail(self._("This is a private file"))

        json_data = self.api_request(
            "GetUrl",
            file_id=file_id,
            free_download_key=None,
            captcha_challenge=None,
            captcha_response=None,
            auth_token=self.account.info["data"]["token"],
        )

        self.link = json_data["url"]
