# -*- coding: utf-8 -*-

import json
import re

from ..anticaptchas.HCaptcha import HCaptcha
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class NitroflareCom(SimpleDownloader):
    __name__ = "NitroflareCom"
    __type__ = "downloader"
    __version__ = "0.42"
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
    LINK_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'

    DIRECT_LINK = False
    DISPOSITION = False

    PREMIUM_ONLY_PATTERN = r"This file is available with Premium only"
    DL_LIMIT_PATTERN = r"You have to wait \d+ minutes to download your next file."

    URL_REPLACEMENTS = [(r"nitro\.download", "nitroflare.com")]

    # See https://nitroflare.com/member?s=general-api
    API_URL = "https://nitroflare.com/api/v2/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.search(self.__pattern__, url).group("ID")

        api_data = self.api_request("getFileInfo", files=file_id)

        if api_data["type"] == "success":
            fileinfo = api_data["result"]["files"][file_id]
            info["status"] = 2 if fileinfo["status"] == "online" else 1
            info["name"] = fileinfo["name"]
            info["size"] = fileinfo["size"]  #: In bytes
            info["post_url"] = fileinfo["url"]

        return info

    def handle_free(self, pyfile):
        #: Used here to load the cookies which will be required later
        self.load(
            "https://nitroflare.com/ajax/setCookie.php",
            post={"fileId": self.info["pattern"]["ID"]},
        )

        self.data = self.load(self.info["post_url"], post={"goToFreePage": ""})

        try:
            wait_time = int(re.search(r"var timerSeconds = (\d+);", self.data).group(1))

        except (IndexError, ValueError, AttributeError):
            wait_time = 120

        data = self.load(
            "https://nitroflare.com/ajax/freeDownload.php",
            post={"method": "startTimer", "fileId": self.info["pattern"]["ID"]},
            ref=self.req.last_effective_url
        )

        self.set_wait(wait_time)

        self.check_errors(data=data)

        inputs = {"method": "fetchDownload"}

        recaptcha = ReCaptcha(pyfile)
        recaptcha_key = recaptcha.detect_key()
        if recaptcha_key:
            self.captcha = recaptcha
            response = self.captcha.challenge(recaptcha_key)
            inputs["g-recaptcha-response"] = response
        else:
            hcaptcha = HCaptcha(pyfile)
            hcaptcha_key = hcaptcha.detect_key()
            if hcaptcha_key:
                self.captcha = hcaptcha
                response = self.captcha.challenge(hcaptcha_key)
                inputs["g-recaptcha-response"] = inputs["h-captcha-response"] = response
            else:
                response = self.captcha.decrypt(
                    "https://nitroflare.com/plugins/cool-captcha/captcha.php"
                )

        inputs["captcha"] = response

        self.wait()

        self.data = self.load(
            "https://nitroflare.com/ajax/freeDownload.php", post=inputs
        )

        if "The captcha wasn't entered correctly" in self.data:
            self.retry_captcha()

        return super().handle_free(pyfile)

    def handle_premium(self, pyfile):
        api_data = self.api_request(
            "getDownloadLink",
            file=self.info["pattern"]["ID"],
            user=self.account.user,
            premiumKey=self.account.get_login("password"),
        )

        if api_data["type"] == "success":
            pyfile.name = api_data["result"]["name"]
            pyfile.size = int(api_data["result"]["size"])
            self.link = api_data["result"]["url"]

        else:
            self.fail(api_data["message"])
