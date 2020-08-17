# -*- coding: utf-8 -*-

import base64
import re
import time
from datetime import timedelta

from pyload.core.network.request_factory import get_url

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class ShareonlineBiz(SimpleDownloader):
    __name__ = "ShareonlineBiz"
    __type__ = "downloader"
    __version__ = "0.67"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(share-online\.biz|egoshare\.com)/(download\.php\?id=|dl/)(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Shareonline.biz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("spoob", "spoob@pyload.net"),
        ("mkaay", "mkaay@mkaay.de"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://www.share-online.biz/dl/\g<ID>")]

    CHECK_TRAFFIC = True

    ERROR_PATTERN = r'<p class="b">Information:</p>\s*<div>\s*<strong>(.*?)</strong>'

    @classmethod
    def api_info(cls, url):
        info = {}
        field = get_url(
            "http://api.share-online.biz/linkcheck.php",
            get={"md5": "1", "links": re.match(cls.__pattern__, url).group("ID")},
        ).split(";")
        try:
            if field[1] == "OK":
                info["fileid"] = field[0]
                info["status"] = 2
                info["name"] = field[2]
                info["size"] = field[3]  #: In bytes
                info["md5"] = field[4].strip().lower().replace("\n\n", "")  #: md5

            elif field[1] in ("DELETED", "NOTFOUND"):
                info["status"] = 1

        except IndexError:
            pass

        return info

    def setup(self):
        self.resume_download = self.premium
        self.multi_dl = False

    def handle_captcha(self):
        self.captcha = ReCaptcha(self.pyfile)
        response, challenge = self.captcha.challenge()

        m = re.search(r"var wait=(\d+);", self.data)
        self.set_wait(int(m.group(1)) if m else 30)

        res = self.load(
            "{}/free/captcha/{}".format(self.pyfile.url, int(time.time() * 1000)),
            post={
                "dl_free": "1",
                "recaptcha_challenge_field": challenge,
                "recaptcha_response_field": response,
            },
        )
        if res != "0":
            self.captcha.correct()
            return res
        else:
            self.retry_captcha()

    def handle_free(self, pyfile):
        self.wait(3)

        self.data = self.load(
            "{}/free/".format(pyfile.url), post={"dl_free": "1", "choice": "free"}
        )

        self.check_errors()

        res = self.handle_captcha()
        self.link = base64.b64decode(res)

        if not self.link.startswith("http://"):
            self.error(self._("Invalid url"))

        self.wait()

    def check_download(self):
        check = self.scan_download(
            {
                "cookie": re.compile(r'<div id="dl_failure"'),
                "fail": re.compile(r"<title>Share-Online"),
            }
        )

        if check == "cookie":
            self.retry_captcha(5, 60, self._("Cookie failure"))

        elif check == "fail":
            self.retry_captcha(
                5, timedelta(minutes=5).seconds, self._("Download failed")
            )

        return SimpleDownloader.check_download(self)

    #: Should be working better loading (account) api internally
    def handle_premium(self, pyfile):
        self.api_data = dlinfo = {}

        html = self.load(
            "https://api.share-online.biz/account.php",
            get={
                "username": self.account.user,
                "password": self.account.get_login("password"),
                "act": "download",
                "lid": self.info["fileid"],
            },
        )

        self.log_debug(html)

        for line in html.splitlines():
            try:
                key, value = line.split(": ")
                dlinfo[key.lower()] = value

            except ValueError:
                pass

        if dlinfo["status"] != "online":
            self.offline()
        else:
            pyfile.name = dlinfo["name"]
            pyfile.size = int(dlinfo["size"])

            self.link = dlinfo["url"]

            if self.link == "server_under_maintenance":
                self.temp_offline()
            else:
                self.multi_dl = True

    def check_errors(self):
        m = re.search(r"/failure/(.*?)/", self.req.last_effective_url)
        if m is None:
            self.info.pop("error", None)
            return

        errmsg = m.group(1).lower()

        try:
            self.log_error(errmsg, re.search(self.ERROR_PATTERN, self.data).group(1))

        except Exception:
            self.log_error(self._("Unknown error occurred"), errmsg)

        if errmsg == "invalid":
            self.fail(self._("File not available"))

        elif errmsg in ("freelimit", "size", "proxy"):
            self.fail(self._("Premium account needed"))

        elif errmsg in ("expired", "server"):
            self.retry(wait=600, msg=errmsg)

        elif errmsg == "full":
            self.fail(self._("Server is full"))

        elif "slot" in errmsg:
            self.wait(3600, reconnect=True)
            self.restart(errmsg)

        else:
            self.wait(60, reconnect=True)
            self.restart(errmsg)
