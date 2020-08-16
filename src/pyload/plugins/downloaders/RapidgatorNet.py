# -*- coding: utf-8 -*-
import json
import re
from datetime import timedelta

import pycurl
from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import seconds

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..base.simple_downloader import SimpleDownloader


class RapidgatorNet(SimpleDownloader):
    __name__ = "RapidgatorNet"
    __type__ = "downloader"
    __version__ = "0.54"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:rapidgator\.net|rg\.to)/file/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Rapidgator.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("chrox", None),
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaCode", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    COOKIES = [("rapidgator.net", "lang", "en")]

    NAME_PATTERN = r"<title>Download file (?P<N>.*)</title>"
    SIZE_PATTERN = r"File size:\s*<strong>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</strong>"
    OFFLINE_PATTERN = r">(File not found|Error 404)"

    JSVARS_PATTERN = r"\s+var\s*(startTimerUrl|getDownloadUrl|captchaUrl|fid|secs)\s*=\s*\'?(.*?)\'?;"

    PREMIUM_ONLY_PATTERN = (
        r"You can download files up to|This file can be downloaded by premium only<"
    )
    DOWNLOAD_LIMIT_ERROR_PATTERN = (
        r"You have reached your (daily|hourly) downloads limit"
    )
    IP_BLOCKED_ERROR_PATTERN = (
        r"You can`t download more than 1 file at a time in free mode\." ""
    )
    WAIT_PATTERN = r"(?:Delay between downloads must be not less than|Try again in).+"

    LINK_FREE_PATTERN = r"return \'(http://\w+.rapidgator.net/.*)\';"

    RECAPTCHA_PATTERN = r'"http://api\.recaptcha\.net/challenge\?k=(.*?)"'
    ADSCAPTCHA_PATTERN = r'(http://api\.adscaptcha\.com/Get\.aspx[^"\']+)'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.script\?k=(.*?)"'

    URL_REPLACEMENTS = [
        (r"//(?:www\.)?rg\.to/", "//rapidgator.net/"),
        (r"(//rapidgator.net/file/[0-9A-z]+).*", r"\1"),
    ]

    API_URL = "https://rapidgator.net/api/"

    def api_response(self, method, **kwargs):
        try:
            html = self.load(self.API_URL + method, get=kwargs)
            json_data = json.loads(html)
            status = json_data["response_status"]
            message = json_data["response_details"]

        except BadHeader as exc:
            status = exc.code
            message = exc.message

        if status == 200:
            return json_data["response"]

        elif status == 404:
            self.offline()

        elif status == 423:
            self.restart(message, premium=False)

        else:
            self.account.relogin()
            self.retry(wait=60)

    def setup(self):
        self.resume_download = self.multi_dl = self.premium
        self.chunk_limit = -1 if self.premium else 1

    def handle_premium(self, pyfile):
        json_data = self.api_response(
            "file/info", sid=self.account.info["data"]["sid"], url=pyfile.url
        )

        self.info["md5"] = json_data["hash"]
        pyfile.name = json_data["filename"]
        pyfile.size = json_data["size"]

        json_data = self.api_response(
            "file/download", sid=self.account.info["data"]["sid"], url=pyfile.url
        )
        self.link = json_data["url"]

    def check_errors(self):
        SimpleDownloader.check_errors(self)
        m = re.search(self.DOWNLOAD_LIMIT_ERROR_PATTERN, self.data)
        if m is not None:
            self.log_warning(m.group(0))
            if m.group(1) == "daily":
                wait_time = seconds.to_midnight()
            else:
                wait_time = timedelta(hours=1).seconds

            self.retry(wait=wait_time, msg=m.group(0))

        m = re.search(self.IP_BLOCKED_ERROR_PATTERN, self.data)
        if m is not None:
            msg = self._(
                "You can't download more than one file within a certain time period in free mode"
            )
            self.log_warning(msg)
            self.retry(wait=timedelta(hours=24).seconds, msg=msg)

    def handle_free(self, pyfile):
        jsvars = dict(re.findall(self.JSVARS_PATTERN, self.data))
        self.log_debug(jsvars)

        url = "https://rapidgator.net{}?fid={}".format(
            jsvars.get("startTimerUrl", "/download/AjaxStartTimer"), jsvars["fid"]
        )
        jsvars.update(self.get_json_response(url))

        self.wait(jsvars.get("secs", 180), False)

        url = "https://rapidgator.net{}?sid={}".format(
            jsvars.get("getDownloadUrl", "/download/AjaxGetDownloadLink"), jsvars["sid"]
        )
        jsvars.update(self.get_json_response(url))

        url = "https://rapidgator.net{}".format(
            jsvars.get("captchaUrl", "/download/captcha")
        )
        self.data = self.load(url, ref=pyfile.url)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            # self.link = m.group(1)
            self.download(m.group(1), ref=url)

        else:
            captcha = self.handle_captcha()

            if not captcha:
                self.error(self._("Captcha pattern not found"))

            response, challenge = captcha.challenge()

            if isinstance(captcha, ReCaptcha):
                post_params = {"g-recaptcha-response": response}

            elif isinstance(captcha, SolveMedia):
                post_params = {
                    "adcopy_challenge": challenge,
                    "adcopy_response": response,
                }

            post_params["DownloadCaptchaForm[verifyCode]"] = response
            self.data = self.load(url, post=post_params, ref=url)

            if "The verification code is incorrect" in self.data:
                self.retry_captcha()

            else:
                m = re.search(self.LINK_FREE_PATTERN, self.data)
                if m is not None:
                    # self.link = m.group(1)
                    self.download(m.group(1), ref=url)

    def handle_captcha(self):
        for klass in (ReCaptcha, SolveMedia):
            captcha = klass(self.pyfile)
            if captcha.detect_key():
                self.captcha = captcha
                return captcha

    def get_json_response(self, url):
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        res = self.load(url, ref=self.pyfile.url)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        if not res.startswith("{"):
            self.retry()
        self.log_debug(url, res)
        return json.loads(res)
