# -*- coding: utf-8 -*-

import json
import random
import re

from pyload.core.network.request_factory import get_url

from ..base.simple_downloader import SimpleDownloader


def gen_r():
    return "0." + "".join(random.choice("0123456789") for x in range(16))


class TenluaVn(SimpleDownloader):
    __name__ = "TenluaVn"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?tenlua\.vn(?!/folder)/.+?/(?P<ID>[0-9a-f]+)/"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Tenlua.vn downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://api2.tenlua.vn/"

    @classmethod
    def api_response(cls, method, **kwargs):
        kwargs["a"] = method
        sid = kwargs.pop("sid", None)
        return json.loads(
            get_url(
                cls.API_URL,
                get={"sid": sid} if sid is not None else {},
                post=json.dumps([kwargs]),
            )
        )

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group("ID")
        file_info = cls.api_response(
            "filemanager_builddownload_getinfo", n=file_id, r=gen_r()
        )[0]

        if file_info["type"] == "none":
            return {"status": 1}

        else:
            return {
                "name": file_info["n"],
                "size": file_info["real_size"],
                "status": 2,
                "tenlua": {
                    "link": file_info["dlink"],
                    "password": bool(file_info["passwd"]),
                },
            }

    def handle_free(self, pyfile):
        self.handle_download()

    def handle_premium(self, pyfile):
        sid = self.account.info["data"]["sid"]
        self.handle_download(sid)

    def handle_download(self, sid=None):
        if self.info["tenlua"]["password"]:
            password = self.get_password()
            if password:
                file_id = self.info["pattern"]["ID"]
                args = dict(n=file_id, p=password, r=gen_r())
                if sid is not None:
                    args["sid"] = sid

                password_status = self.api_response(
                    "filemanager_builddownload_checkpassword", **args
                )
                if password_status["status"] == "0":
                    self.fail(self._("Wrong password"))

                else:
                    url = password_status["url"]

            else:
                self.fail(self._("Download is password protected"))

        else:
            url = self.info["tenlua"]["link"]

        if sid is None:
            self.wait(30)

        self.link = url
