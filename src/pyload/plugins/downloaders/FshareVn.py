# -*- coding: utf-8 -*-
import json
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


def double_decode(m):
    return m.group(1).decode("raw_unicode_escape")


class FshareVn(SimpleDownloader):
    __name__ = "FshareVn"
    __type__ = "downloader"
    __version__ = "0.32"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?fshare\.vn/file/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """FshareVn downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = (
        r'<i class="material-icons">insert_drive_file</i>\s*(?P<N>.+?)\s*</div>'
    )
    SIZE_PATTERN = (
        r'<i class="material-icons">save</i>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)\s*</div>'
    )
    OFFLINE_PATTERN = r"Tập tin của bạn yêu cầu không tồn tại"

    NAME_REPLACEMENTS = [("(.*)", double_decode)]

    URL_REPLACEMENTS = [("http://", "https://")]

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('class="password-form"')
        if action is not None:
            password = self.get_password()
            if password:
                inputs["DownloadPasswordForm[password]"] = password

            else:
                self.fail(self._("Download is password protected"))

            url = urllib.parse.urljoin(pyfile.url, action)

            self.data = self.load(url, post=inputs)
            if r"Sai mật khẩu" in self.data:
                self.fail(self._("Wrong password"))

        action, inputs = self.parse_html_form(
            'id="form-download"', input_names={"withFcode5": "0"}
        )
        url = urllib.parse.urljoin(pyfile.url, action)

        if not inputs:
            self.error(self._("Free Download form not found"))

        self.data = self.load(url, post=inputs)

        try:
            json_data = json.loads(self.data)

        except Exception:
            self.fail(self._("Expected JSON data"))

        err_msg = json_data.get("msg")
        if err_msg:
            self.fail(err_msg)

        elif "url" not in json_data:
            self.fail(self._("Unexpected response"))

        wait_time = json_data.get("wait_time", None)
        wait_time = 35 if wait_time is None else int(wait_time)
        self.wait(wait_time)

        self.link = json_data["url"]

    def handle_premium(self, pyfile):
        self.handle_free(pyfile)
