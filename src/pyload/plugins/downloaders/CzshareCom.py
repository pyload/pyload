# -*- coding: utf-8 -*-

import re

from pyload.core.utils import parse
from pyload.core.utils.convert import to_bytes

from ..base.simple_downloader import SimpleDownloader


class CzshareCom(SimpleDownloader):
    __name__ = "CzshareCom"
    __type__ = "downloader"
    __version__ = "1.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(czshare|sdilej)\.(com|cz)/(\d+/|download\.php\?).+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """CZshare.com downloader plugin, now Sdilej.cz"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("ondrej", "git@ondrej.it"),
    ]

    NAME_PATTERN = r'<div class="tab" id="parameters">\s*<p>\s*Cel. n.zev: <a href=.*?>(?P<N>.+?)</a>'
    SIZE_PATTERN = r'<div class="tab" id="category">(?:\s*<p>[^\n]*</p>)*\s*Velikost:\s*(?P<S>[\d .,]+)(?P<U>[\w^_]+)\s*</div>'
    OFFLINE_PATTERN = r'<div class="header clearfix">\s*<h2 class="red">'

    SIZE_REPLACEMENTS = [(" ", "")]
    URL_REPLACEMENTS = [
        (r"http://[^/]*/download.php\?.*?id=(\w+).*", r"http://sdilej.cz/\1/x/")
    ]

    CHECK_TRAFFIC = True

    FREE_URL_PATTERN = r'<a href="(.+?)" class="page-download">[^>]*alt="(.+?)" /></a>'
    FREE_FORM_PATTERN = r'<form action="download\.php" method="post">\s*<img src="captcha\.php" id="captcha" />(.*?)</form>'
    PREMIUM_FORM_PATTERN = r'<form action="/profi_down\.php" method="post">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="(.+?)" value="(.+?)"[^>]*/>'
    MULTIDL_PATTERN = r"<p><font color=\'red\'>Z.*?PROFI.</font></p>"
    USER_CREDIT_PATTERN = r'<div class="credit">\s*kredit: <strong>([\d .,]+)(\w+)</strong>\s*</div><!-- .credit -->'

    def out_of_traffic(self):
        #: Check if user logged in
        m = re.search(self.USER_CREDIT_PATTERN, self.data)
        if m is None:
            self.account.relogin()
            self.data = self.load(self.pyfile.url)
            m = re.search(self.USER_CREDIT_PATTERN, self.data)
            if m is None:
                return True

        #: Check user credit
        try:
            credit = parse.bytesize(m.group(1).replace(" ", ""), m.group(2))
            self.log_info(
                self._("Premium download for {} KiB of Credit").format(
                    self.pyfile.size / 1024
                )
            )
            self.log_info(
                self._("User {} has {} KiB left").format(
                    self.account.user, credit / 1024
                )
            )
            if credit < self.pyfile.size:
                self.log_info(
                    self._("Not enough credit to download file: {}").format(
                        self.pyfile.name
                    )
                )
                return True

        except Exception as exc:
            #: let's continue and see what happens...
            self.log_error(exc)

        return False

    def handle_premium(self, pyfile):
        try:
            form = re.search(self.PREMIUM_FORM_PATTERN, self.data, re.S).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))

        except Exception as exc:
            self.log_error(exc)
            self.restart(premium=False)

        #: Download the file, destination is determined by pyLoad
        self.download("http://sdilej.cz/profi_down.php", post=inputs, disposition=True)

    def handle_free(self, pyfile):
        #: Get free url
        m = re.search(self.FREE_URL_PATTERN, self.data)
        if m is None:
            self.error(self._("FREE_URL_PATTERN not found"))

        parsed_url = "http://sdilej.cz" + m.group(1)

        self.log_debug("PARSED_URL:" + parsed_url)

        #: Get download ticket and parse html
        self.data = self.load(parsed_url)
        if re.search(self.MULTIDL_PATTERN, self.data):
            self.retry(5 * 60, 12, self._("Download limit reached"))

        try:
            form = re.search(self.FREE_FORM_PATTERN, self.data, re.S).group(1)
            inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
            pyfile.size = int(inputs["size"])

        except Exception as exc:
            self.log_error(exc)
            self.error(self._("Form"))

        #: Get and decrypt captcha
        captcha_url = "http://sdilej.cz/captcha.php"
        inputs["captchastring2"] = self.captcha.decrypt(captcha_url)
        self.data = self.load(parsed_url, post=inputs)

        if "<li>Zadaný ověřovací kód nesouhlasí!</li>" in self.data:
            self.retry_captcha()

        elif re.search(self.MULTIDL_PATTERN, self.data):
            self.retry(5 * 60, 12, self._("Download limit reached"))

        else:
            self.captcha.correct()

        m = re.search("countdown_number = (\d+);", self.data)
        self.set_wait(int(m.group(1)) if m else 50)

        #: Download the file, destination is determined by pyLoad
        self.log_debug("WAIT URL", self.req.lastEffectiveURL)

        m = re.search("free_wait.php\?server=(.*?)&(.*)", self.req.lastEffectiveURL)
        if m is None:
            self.error(self._("Download URL not found"))

        self.link = "http://{}/download.php?{}".format(m.group(1), m.group(2))

        self.wait()

    def check_download(self):
        #: Check download
        check = self.scan_download(
            {
                "temp offline": re.compile(rb"^Soubor je do.*asn.* nedostupn.*$"),
                "credit": re.compile(rb"^Nem.*te dostate.*n.* kredit.$"),
                "multi-dl": re.compile(to_bytes(self.MULTIDL_PATTERN)),
                "captcha": to_bytes("<li>Zadaný ověřovací kód nesouhlasí!</li>"),
            }
        )

        if check == "temp offline":
            self.fail(self._("File not available - try later"))

        elif check == "credit":
            self.restart(premium=False)

        elif check == "multi-dl":
            self.retry(5 * 60, 12, self._("Download limit reached"))

        elif check == "captcha":
            self.retry_captcha()

        return super().check_download()
