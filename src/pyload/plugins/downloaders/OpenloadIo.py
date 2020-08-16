# -*- coding: utf-8 -*-

import json
import re

from pyload.core.network.request_factory import get_url

from ..base.simple_downloader import SimpleDownloader


class OpenloadIo(SimpleDownloader):
    __name__ = "OpenloadIo"
    __type__ = "downloader"
    __version__ = "0.20"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?openload\.(co|io)/(f|embed)/(?P<ID>[\w\-]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Openload.co downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    OFFLINE_PATTERN = r">We are sorry"

    # The API reference, that this implementation uses is available at
    # https://openload.co/api
    API_URL = "https://api.openload.co/1"

    @classmethod
    def api_response(cls, file_id, method, **kwargs):
        kwargs["file"] = file_id
        return json.loads(get_url(cls.API_URL + "/file/" + method, get=kwargs))

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group("ID")
        info_json = cls.api_response(file_id, "info")
        file_info = info_json["result"][file_id]

        return {"name": file_info["name"], "size": file_info["size"]}

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        ticket_json = self.api_response(file_id, "dlticket")

        if ticket_json["status"] != 200:
            self.log_error(ticket_json["msg"])

        if ticket_json["status"] == 404:
            self.offline(ticket_json["msg"])

        elif ticket_json["status"] == 509:
            self.temp_offline(ticket_json["msg"])

        elif ticket_json["status"] != 200:
            self.fail(ticket_json["msg"])

        self.wait(ticket_json["result"]["wait_time"])

        # check if a captcha is required for this download
        captcha_response = ""
        if (
            "captcha_url" in ticket_json["result"]
            and ticket_json["result"]["captcha_url"]
        ):
            captcha_url = ticket_json["result"]["captcha_url"]
            self.log_debug(f"This download requires a captcha solution: {captcha_url}")
            captcha_response = self.captcha.decrypt(captcha_url)

        ticket = ticket_json["result"]["ticket"]

        download_json = self.api_response(
            file_id, "dl", ticket=ticket, captcha_response=captcha_response
        )

        # check download link request result status
        if download_json["status"] == 403:
            # wrong captcha, get new captcha and try again
            self.retry_captcha()

        elif download_json["status"] == 200:
            self.link = download_json["result"]["url"]

        else:
            # no status 403 or 200 means getting the download url failed, abort
            self.fail(download_json["msg"])
