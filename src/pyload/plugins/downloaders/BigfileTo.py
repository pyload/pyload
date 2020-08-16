# -*- coding: utf-8 -*-

import json
import re
from datetime import timedelta

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class BigfileTo(SimpleDownloader):
    __name__ = "BigfileTo"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:uploadable\.ch|bigfile.to)/file/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """bigfile.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://www.bigfile.to/file/\g<ID>")]

    INFO_PATTERN = r"div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>[\d.]+) (?P<U>\w+)\)</span><"

    OFFLINE_PATTERN = r">(File not available|This file is no longer available)"
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'

    WAIT_PATTERN = r">Please wait[^<]+"

    RECAPTCHA_KEY = "6LfZ0RETAAAAAOjhYT7V9ukeCT3wWccw98uc50vu"

    def handle_free(self, pyfile):
        #: Click the "free user" button and wait
        json_data = json.loads(self.load(pyfile.url, post={"downloadLink": "wait"}))

        self.wait(json_data["waitTime"])

        #: Make the ReCaptcha appear and show it the pyload interface
        json_data = json.loads(self.load(pyfile.url, post={"checkDownload": "check"}))
        if json_data["success"] == "showCaptcha":
            self.captcha = ReCaptcha(pyfile)

            response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

            #: Submit the captcha solution
            json_data = json.loads(
                self.load(
                    "https://www.bigfile.to/checkReCaptcha.php",
                    post={
                        "recaptcha_challenge_field": challenge,
                        "recaptcha_response_field": response,
                        "recaptcha_shortencode_field": self.info["pattern"]["ID"],
                    },
                )
            )
            self.log_debug("json_data", json_data)
            if json_data["success"] != 1:
                self.retry_captcha()

        #: Get ready for downloading
        self.load(pyfile.url, post={"downloadLink": "show"})

        #: Download the file
        self.download(pyfile.url, post={"download": "normal"}, disposition=True)

    def check_download(self):
        if self.scan_download({"wait": re.compile("Please wait for")}):
            self.log_info(self._("Downloadlimit reached, please wait or reconnect"))
            self.wait(timedelta(hours=1).seconds, True)
            self.retry()

        return SimpleDownloader.check_download(self)
