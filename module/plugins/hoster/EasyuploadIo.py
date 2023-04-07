# -*- coding: utf-8 -*-

import json
import re
import urllib

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.SimpleHoster import SimpleHoster


class EasyuploadIo(SimpleHoster):
    __name__ = "EasyuploadIo"
    __type__ = "hoster"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?easyupload\.io/(?P<ID>\w+)"
    __config__ = [
        ("activated", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Easyupload.io hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"<h4>(?P<N>.+?)</h4>"
    SIZE_PATTERN = r">Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r"<h4>FILE NOT FOUND</h4>"

    RECAPTCHA_PATTERN = r"grecaptcha.execute\('((?:[\w\-]|%[0-9a-fA-F]{2})+)'"

    def setup(self):
        self.multiDL = True

    def handle_free(self, pyfile):
        password_protected = "$('#password-modal').modal('open');" in self.data

        m = re.search(r'url: "(https://\w+\.easyupload\.io/action\.php)"', self.data)
        if m is None:
            self.fail("action URL not found")

        else:
            action_url = m.group(1)

        if password_protected:
            password = self.get_password()
            if not password:
                self.fail(_("Password required"))
        else:
            password = ""

        m = re.search(self.RECAPTCHA_PATTERN, self.data)
        if m is None:
            self.fail(_("ReCaptcha key not found"))

        else:
            recaptcha_key = urllib.unquote(m.group(1).strip())

        self.captcha = ReCaptcha(pyfile)
        response = self.captcha.challenge(recaptcha_key, version="2invisible")

        data = self.load(
            action_url,
            ref="https://easyupload.io/",
            post={
                "type": "download-token",
                "url": self.info["pattern"]["ID"],
                "value": password,
                "captchatoken": response,
                "method": "regular",
            },
        )

        json_data = json.loads(data)
        if json_data.get("status") == True:
            self.link = json_data["download_link"]

        elif password_protected:
            self.fail(_("Wrong password"))

        else:
            self.fail(json_data["data"])
