# -*- coding: utf-8 -*-

import json
import re

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.SolveMedia import SolveMedia
from ..base.simple_downloader import SimpleDownloader


class FikperCom(SimpleDownloader):
    __name__ = "FikperCom"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://fikper\.com/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Fikper.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    SOLVEMEDIA_KEY = "U0PGYjYQo61wWfWxQ43vpsJrUQSpCiuY"
    API_URL = "https://sapi.fikper.com/"

    DIRECT_LINK = False

    # See https://sapi.fikper.com/api/reference/
    def api_request(self, method, api_key=None, **kwargs):
        if api_key is not None:
            self.req.http.c.setopt(pycurl.HTTPHEADER, [f"x-api-key: {api_key}"])

        try:
            json_data = self.load(self.API_URL + method, post=kwargs)
            return json.loads(json_data)

        except json.JSONDecodeError:
            return json_data

        except BadHeader as exc:
            return json.loads(exc.content)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")
        file_info = self.api_request("", fileHashName=file_id)
        if file_info.get("code") == 404:
            info["status"] = 1
        else:
            info["status"] = 2
            info["name"] = file_info["name"]
            info["size"] = file_info["size"]
            info["download_token"] = file_info["downloadToken"]
            info["delay_dime"] = file_info["delayTime"]
            info["dl_limit_delay"] = int(file_info.get("remainingDelay", 0))

        return info

    def handle_free(self, pyfile):
        dl_limit_delay = self.info["dl_limit_delay"]
        if dl_limit_delay:
            self.wait(
                dl_limit_delay,
                reconnect=dl_limit_delay > self.config.get("max_wait", 10) * 60,
            )
            self.restart(self._("Download limit exceeded"))

        self.captcha = SolveMedia(pyfile)
        self.set_wait(self.info["delay_dime"] / 1000)
        response, challenge = self.captcha.challenge(self.SOLVEMEDIA_KEY)
        self.wait()
        json_data = self.api_request(
            "",
            fileHashName=self.info["pattern"]["ID"],
            downloadToken=self.info["download_token"],
            captchaValue=response,
            challenge=challenge
        )
        if "directLink" in json_data:
            self.link = json_data["directLink"]

    def handle_premium(self, pyfile):
        file_id = self.info["pattern"]["ID"]
        api_key = self.account.info["login"]["password"]
        api_data = self.api_request(f"api/file/download/{file_id}", api_key=api_key)
        if self.req.code != 200:
            self.log_error(self._("API error"), api_data)

        else:
            self.link = api_data
