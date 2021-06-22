# -*- coding: utf-8 -*-

import json

import pycurl

from ..base.multi_downloader import MultiDownloader


class MultishareCz(MultiDownloader):
    __name__ = "MultishareCz"
    __type__ = "downloader"
    __version__ = "0.49"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?multishare\.cz/stahnout/(?P<ID>\d+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """MultiShare.cz multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    #: See https://multishare.cz/api/
    API_URL = "https://www.multishare.cz/api/"

    def api_request(self, method, **kwargs):
        get = {"sub": method}
        get.update(kwargs)
        self.req.http.c.setopt(pycurl.USERAGENT, "JDownloader")
        json_data = self.load(self.API_URL, get=get)

        if not json_data.startswith("{"):
            if json_data.startswith("ERR:"):
                json_data = json_data[4:].strip()
            return {"err": json_data}

        else:
            return json.loads(json_data)

    def handle_premium(self, pyfile):
        api_data = self.api_request("check-file", link=pyfile.url)
        if "err" in api_data:
            if "Given link is dead" in api_data["err"]:
                self.offline()

            else:
                self.fail(api_data["err"])

        pyfile.name = api_data["file_name"]
        pyfile.size = api_data["file_size"]

        api_data = self.api_request(
            "download-link",
            link=pyfile.url,
            login=self.account.user,
            password=self.account.info["login"]["password"],
        )

        self.chunk_limit = api_data["chunks"]
        self.link = api_data["link"]
