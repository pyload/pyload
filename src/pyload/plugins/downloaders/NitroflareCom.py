# -*- coding: utf-8 -*-

import json
import re

from pyload.core.network.request_factory import get_url

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class NitroflareCom(SimpleDownloader):
    __name__ = "NitroflareCom"
    __type__ = "downloader"
    __version__ = "0.30"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:nitro\.download|nitroflare\.com)/view/(?P<ID>[\w^_]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Nitroflare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("sahil", "sahilshekhawat01@gmail.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    INFO_PATTERN = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r">File doesn\'t exist"

    LINK_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'

    DIRECT_LINK = False

    PREMIUM_ONLY_PATTERN = r"This file is available with Premium only"
    DL_LIMIT_PATTERN = r"You have to wait \d+ minutes to download your next file."

    URL_REPLACEMENTS = [(r"nitro\.download", "nitroflare.com")]

    @classmethod
    def api_info(cls, url):
        info = {}
        file_id = re.search(cls.__pattern__, url).group("ID")

        data = json.loads(
            get_url("https://nitroflare.com/api/v2/getFileInfo", get={"files": file_id})
        )

        if data["type"] == "success":
            fileinfo = data["result"]["files"][file_id]
            info["status"] = 2 if fileinfo["status"] == "online" else 1
            info["name"] = fileinfo["name"]
            info["size"] = fileinfo["size"]  #: In bytes

        return info

    def handle_free(self, pyfile):
        #: Used here to load the cookies which will be required later
        self.load(
            "http://nitroflare.com/ajax/setCookie.php",
            post={"fileId": self.info["pattern"]["ID"]},
        )

        self.data = self.load(pyfile.url, post={"goToFreePage": ""})

        try:
            wait_time = int(re.search(r"var timerSeconds = (\d+);", self.data).group(1))

        except (IndexError, ValueError):
            wait_time = 120

        recaptcha = ReCaptcha(pyfile)
        recaptcha_key = recaptcha.detect_key()

        self.data = self.load(
            "http://nitroflare.com/ajax/freeDownload.php",
            post={"method": "startTimer", "fileId": self.info["pattern"]["ID"]},
        )

        self.check_errors()

        self.set_wait(wait_time)

        inputs = {"method": "fetchDownload"}

        if recaptcha_key:
            self.captcha = recaptcha
            response, _ = self.captcha.challenge(recaptcha_key)
            inputs["g-recaptcha-response"] = response

        else:
            response = self.captcha.decrypt(
                "http://nitroflare.com/plugins/cool-captcha/captcha.php"
            )

        inputs["captcha"] = response

        self.wait()

        self.data = self.load(
            "http://nitroflare.com/ajax/freeDownload.php", post=inputs
        )

        if "The captcha wasn't entered correctly" in self.data:
            self.retry_captcha()

        return super().handle_free(pyfile)

    def handle_premium(self, pyfile):
        data = json.loads(
            self.load(
                "https://nitroflare.com/api/v2/getDownloadLink",
                get={
                    "file": self.info["pattern"]["ID"],
                    "user": self.account.user,
                    "premiumKey": self.account.get_login("password"),
                },
            )
        )

        if data["type"] == "success":
            pyfile.name = data["result"]["name"]
            pyfile.size = int(data["result"]["size"])
            self.link = data["result"]["url"]
