# -*- coding: utf-8 -*-

import json
import time

import pycurl

from ..anticaptchas.ReCaptcha import ReCaptcha
from pyload.core.utils import seconds
from ..base.simple_downloader import SimpleDownloader


class RapiduNet(SimpleDownloader):
    __name__ = "RapiduNet"
    __type__ = "downloader"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?rapidu\.net/(?P<ID>\d{10})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Rapidu.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None)]

    COOKIES = [("rapidu.net", "rapidu_lang", "en")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", "https://rapidu.net/\g<ID>")]

    INFO_PATTERN = (
        r'<h1 title="(?P<N>.*)">.*</h1>\s*<small>(?P<S>\d+(\.\d+)?)\s(?P<U>\w+)</small>'
    )
    OFFLINE_PATTERN = r"<h1>404"

    ERROR_PATTERN = r'<div class="error">'

    RECAPTCHA_KEY = r"6LcOuQkUAAAAAF8FPp423qz-U2AXon68gJSdI_W4"

    def setup(self):
        self.resume_download = True
        self.multi_dl = self.premium

    def handle_free(self, pyfile):
        self.req.http.last_url = pyfile.url
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        json_data = self.get_json_response(
            "https://rapidu.net/ajax.php",
            get={"a": "getLoadTimeToDownload"},
            post={"_go": ""},
        )

        if str(json_data["timeToDownload"]) == "stop":
            self.log_warning(self._("You've reach your daily download transfer"))
            self.retry(10, wait=seconds.to_midnight(), msg=self._("You've reach your daily download transfer"))

        self.set_wait(int(json_data["timeToDownload"]) - int(time.time()))

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

        self.wait()

        json_data = self.get_json_response(
            "https://rapidu.net/ajax.php",
            get={"a": "getCheckCaptcha"},
            post={
                "_go": "",
                "captcha1": challenge,
                "captcha2": response,
                "fileId": self.info["pattern"]["ID"],
            },
        )

        if json_data["message"] == "success":
            self.link = json_data["url"]

    def get_json_response(self, *args, **kwargs):
        res = self.load(*args, **kwargs)
        if not res.startswith("{"):
            self.retry()

        self.log_debug(res)

        return json.loads(res)
