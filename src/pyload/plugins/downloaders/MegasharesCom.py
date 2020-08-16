# -*- coding: utf-8 -*-

import re
import time
from datetime import timedelta

from ..base.simple_downloader import SimpleDownloader


class MegasharesCom(SimpleDownloader):
    __name__ = "MegasharesCom"
    __type__ = "downloader"
    __version__ = "0.37"
    __status__ = "testing"

    __pattern__ = (
        r"http://(?:www\.)?(d\d{2}\.)?megashares\.com/((index\.php)?\?d\d{2}=|dl/)\w+"
    )
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Megashares.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    NAME_PATTERN = r'<h1 class="black xxl"[^>]*title="(?P<N>.+?)">'
    SIZE_PATTERN = r'<strong><span class="black">Filesize:</span></strong> (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = (
        r'<dd class="red">(Invalid Link Request|Link has been deleted|Invalid link)'
    )

    LINK_PATTERN = r'<div id="show_download_button_{}".*?>\s*<a href="(.+?)">'

    PASSPORT_LEFT_PATTERN = (
        r"Your Download Passport is: <.*?>(\w+).*?You have.*?<.*?>.*?([\d.]+) (\w+)"
    )
    PASSPORT_RENEW_PATTERN = r"(\d+):<strong>(\d+)</strong>:<strong>(\d+)</strong>"
    REACTIVATE_NUM_PATTERN = r'<input[^>]*id="random_num" value="(\d+)" />'
    REACTIVATE_PASSPORT_PATTERN = r'<input[^>]*id="passport_num" value="(\w+)" />'
    REQUEST_URI_PATTERN = r'var request_uri = "(.+?)";'
    NO_SLOTS_PATTERN = (
        r'<dd class="red">All download slots for this link are currently filled'
    )

    def setup(self):
        self.resume_download = True
        self.multi_dl = self.premium

    def handle_premium(self, pyfile):
        self.handle_download(True)

    def handle_free(self, pyfile):
        if self.NO_SLOTS_PATTERN in self.data:
            self.retry(wait=timedelta(minutes=5).seconds)

        m = re.search(self.REACTIVATE_PASSPORT_PATTERN, self.data)
        if m is not None:
            passport_num = m.group(1)
            request_uri = re.search(self.REQUEST_URI_PATTERN, self.data).group(1)

            random_num = re.search(self.REACTIVATE_NUM_PATTERN, self.data).group(1)

            verifyinput = self.captcha.decrypt(
                "http://d01.megashares.com/index.php",
                get={"secgfx": "gfx", "random_num": random_num},
            )

            self.log_info(
                self._("Reactivating passport {}: {} {}").format(
                    passport_num, random_num, verifyinput
                )
            )

            res = self.load(
                "http://d01.megashares.com{}".format(request_uri),
                get={
                    "rs": "check_passport_renewal",
                    "rsargs[]": verifyinput,
                    "rsargs[]": random_num,
                    "rsargs[]": passport_num,
                    "rsargs[]": "replace_sec_pprenewal",
                    "rsrnd[]": str(int(time.time() * 1000)),
                },
            )

            if "Thank you for reactivating your passport" in res:
                self.captcha.correct()
                self.restart()
            else:
                self.retry_captcha(msg=self._("Failed to reactivate passport"))

        m = re.search(self.PASSPORT_RENEW_PATTERN, self.data)
        if m is not None:
            times = [int(x) for x in m.groups()]
            renew = (
                times[0]
                + timedelta(minutes=times[1]).seconds
                + timedelta(minutes=times[2]).seconds
            )
            self.log_debug(f"Waiting {renew} seconds for a new passport")
            self.retry(wait=renew, msg=self._("Passport renewal"))

        #: Check traffic left on passport
        m = re.search(self.PASSPORT_LEFT_PATTERN, self.data, re.M | re.S)
        if m is None:
            self.fail(self._("Passport not found"))

        self.log_info(self._("Download passport: {}").format(m.group(1)))
        data_left = (
            float(m.group(2)) << 10 ** {"B": 0, "KB": 1, "MB": 2, "GB": 3}[m.group(3)]
        )
        self.log_info(
            self._("Data left: {} {} ({} MiB needed)").format(
                m.group(2), m.group(3), self.pyfile.size // 1_048_576
            )
        )

        if not data_left:
            self.retry(wait=600, msg=self._("Passport renewal"))

        self.handle_download(False)

    def handle_download(self, premium=False):
        m = re.search(self.LINK_PATTERN.format(1 if premium else 2), self.data)
        msg = self._("{} download URL").format("Premium" if premium else "Free")
        if m is None:
            self.error(msg)

        self.link = m.group(1)
        self.log_debug(f"{msg}: {self.link}")
