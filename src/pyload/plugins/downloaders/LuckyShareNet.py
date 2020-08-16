# -*- coding: utf-8 -*-
import json
import re

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class LuckyShareNet(SimpleDownloader):
    __name__ = "LuckyShareNet"
    __type__ = "downloader"
    __version__ = "0.14"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?luckyshare\.net/(?P<ID>\d{10,})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """LuckyShare.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    INFO_PATTERN = r"<h1 class=\'file_name\'>(?P<N>\S+)</h1>\s*<span class=\'file_size\'>Filesize: (?P<S>[\d.,]+)(?P<U>[\w^_]+)</span>"
    OFFLINE_PATTERN = r"There is no such file available"

    def parse_json(self, rep):
        if "AJAX Error" in rep:
            html = self.load(self.pyfile.url)
            m = re.search(r"waitingtime = (\d+);", html)
            if m is not None:
                seconds = int(m.group(1))
                self.log_debug(
                    "You have to wait {} seconds between free downloads".format(seconds)
                )
                self.retry(wait=seconds)
            else:
                self.error(self._("Unable to detect wait time between free downloads"))
        elif "Hash expired" in rep:
            self.retry(msg=self._("Hash expired"))
        return json.loads(rep)

    # TODO: There should be a filesize limit for free downloads
    #       Some files could not be downloaded in free mode
    def handle_free(self, pyfile):
        rep = self.load(
            r"http://luckyshare.net/download/request/type/time/file/"
            + self.info["pattern"]["ID"]
        )

        self.log_debug("JSON: " + rep)

        json_data = self.parse_json(rep)
        self.wait(json_data["time"])

        self.captcha = ReCaptcha(pyfile)

        response, challenge = self.captcha.challenge()
        rep = self.load(
            r"http://luckyshare.net/download/verify/challenge/{}/response/{}/hash/{}".format(
                challenge, response, json_data["hash"]
            )
        )

        self.log_debug("JSON: " + rep)

        if "Verification failed" in rep:
            self.retry_captcha()

        elif "link" in rep:
            self.captcha.correct()
            json_data.update(self.parse_json(rep))
            if json_data["link"]:
                self.link = json_data["link"]
