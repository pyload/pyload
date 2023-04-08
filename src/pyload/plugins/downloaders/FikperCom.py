# -*- coding: utf-8 -*-

import json
import re

from ..anticaptchas.HCaptcha import HCaptcha
from ..base.simple_downloader import SimpleDownloader


class FikperCom(SimpleDownloader):
    __name__ = "FikperCom"
    __type__ = "downloader"
    __version__ = "0.01"
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

    HCAPTCHA_KEY = "ddd70c6f-e4cb-45e2-9374-171fbc0d4137"
    API_URL = "https://sapi.fikper.com/"

    DIRECT_LINK = False

    def api_request(self, *args, **kwargs):
        json_data = self.load(self.API_URL, post=kwargs)
        return json.loads(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")
        file_info = self.api_request(fileHashName=file_id)
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

        self.captcha = HCaptcha(pyfile)
        self.set_wait(self.info["delay_dime"] / 1000)
        response = self.captcha.challenge(self.HCAPTCHA_KEY)
        self.wait()
        json_data = self.api_request(
            fileHashName=self.info["pattern"]["ID"],
            downloadToken=self.info["download_token"],
            recaptcha=response,
        )
        if "directLink" in json_data:
            self.link = json_data["directLink"]
