# -*- coding: utf-8 -*-

import re

from ..base.xfs_downloader import XFSDownloader


class UploadshipCom(XFSDownloader):
    __name__ = "UploadshipCom"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?uploadship\.com/\w{16}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uploadship.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "ozzie.fernandez.isaacs@gmail.com")]

    PLUGIN_DOMAIN = "uploadship.com"

    NAME_PATTERN = r'<span style="display: block; line-height: 17px; word-break: break-all;"><small>(?P<N>.+?)</small></span>'
    SIZE_PATTERN = r'<i class="fa fa-hdd-o" aria-hidden="true"></td><td>((?P<S>[\d.,]+) (?P<U>[\w^_]+)) :'
    WAIT_PATTERN = r"\$\('\.download-timer-seconds'\)\.html\((\d+)\);"

    FORM_INPUTS_MAP = {"d": re.compile(r"^1")}
    LINK_PATTERN = r'href="(.+?)" target="_blank" class="btn btn-go">Click Here To Download'

    ERROR_PATTERN = None

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form(
            self.FORM_PATTERN or "", self.FORM_INPUTS_MAP or {}
        )

        secret = re.search(r'"data": {\r\n"(\w{32})": "(\w{32})"', self.data, re.S)
        if secret is not None:
            get_data = {secret.group(1): secret.group(2)}
            secret_data = self.load(
                "https://www.uploadship.com/" + secret.group(1) + ".php", get=get_data
            )
            inputs[secret.group(1)] = secret_data

        self.handle_captcha(inputs)

        self.data = self.load(
            pyfile.url, post=inputs, ref=self.pyfile.url, redirect=False
        )

        m = re.search(self.LINK_PATTERN, self.data, re.M)
        if m is not None:
            self.link = m.group(1)
