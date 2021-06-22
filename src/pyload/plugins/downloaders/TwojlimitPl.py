# -*- coding: utf-8 -*-
import json

from ..base.multi_downloader import MultiDownloader


class TwojlimitPl(MultiDownloader):
    __name__ = "TwojlimitPl"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Twojlimit.pl multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("synweap15", "pawel@twojlimit.pl")]

    API_URL = "https://crypt.twojlimit.pl"

    API_QUERY = {
        "site": "newtl",
        "output": "json",
        "username": "",
        "password": "",
        "url": "",
    }

    ERROR_CODES = {
        0: "Incorrect login credentials",
        1: "Not enough transfer to download - top-up your account",
        2: "Incorrect / dead link",
        3: "Error connecting to hosting, try again later",
        9: "Premium account has expired",
        15: "Hosting no longer supported",
        80: "Too many incorrect login attempts, account blocked for 24h",
    }

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = -1

    def handle_free(self, pyfile):
        try:
            data = self.run_file_query(pyfile.url, "fileinfo")

        except Exception as exc:
            self.log_error(exc)
            self.temp_offline("Query error #1")

        try:
            json_data = json.loads(data)

        except Exception:
            self.temp_offline("Data not found")

        if "errno" in json_data:
            if json_data["errno"] in self.ERROR_CODES:
                #: Error code in known
                self.fail(self.ERROR_CODES[json_data["errno"]])

            else:
                #: Error code isn't yet added to plugin
                self.fail(
                    json_data["errstring"]
                    or self._("Unknown error (code: {})").format(json_data["errno"])
                )

        if "sdownload" in json_data:
            if json_data["sdownload"] == "1":
                self.fail(
                    self._(
                        "Download from {} is possible only using TwojLimit.pl website directly"
                    ).format(json_data["hosting"])
                )

        pyfile.name = json_data["filename"]
        pyfile.size = json_data["filesize"]

        try:
            self.download(self.run_file_query(pyfile.url, "filedownload"))

        except Exception as exc:
            self.log_error(exc)
            self.temp_offline("Query error #2")

    def run_file_query(self, url, mode=None):
        query = self.API_QUERY.copy()

        query["username"] = self.account.user
        query["password"] = self.account.info["data"]["hash_password"]
        query["url"] = url

        if mode == "fileinfo":
            query["check"] = 2
            query["loc"] = 1

        return self.load(self.API_URL, post=query, redirect=20)
