# -*- coding: utf-8 -*-

import time

import pycurl

from module.network.HTTPRequest import BadHeader

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


class TorboxApp(MultiHoster):
    __name__ = "TorboxApp"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("activated", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Torbox.app multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    # See https://api-docs.torbox.app/
    API_URL = "https://api.torbox.app/v1/api/"

    def api_request(self, method, api_key=None, get={}, post={}):
        if api_key is not None:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + api_key]
            )

        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader as exc:
            json_data = exc.content

        api_data = json.loads(json_data)
        return api_data

    def sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        api_key = self.account.info["login"]["password"]

        post = {"link": pyfile.url}
        password = self.get_password()
        if password:
            post["password"] = password

        api_data = self.api_request("webdl/createwebdownload",
                                    api_key=api_key,
                                    post=post)
        self.check_errors(api_data)

        file_id = api_data["data"]["webdownload_id"]
        file_hash = api_data["data"]["hash"]

        api_data = self.api_request("webdl/checkcached",
                                    api_key=api_key,
                                    get={
                                        "hash": file_hash,
                                        "format": "object",
                                        "bypass_cache": True,
                                    })

        if api_data.get("success", False) and api_data.get("data"):
            pyfile.name = api_data["data"][file_hash]["name"]
            pyfile.size = api_data["data"][file_hash]["size"]

        else:
            pyfile.set_custom_status("web caching")
            pyfile.set_progress(0)
            while True:
                api_data = self.api_request("webdl/mylist",
                                            api_key=api_key,
                                            get={
                                                "id": file_id,
                                                "bypass_cache": True,
                                            })

                file_size = api_data["data"].get("size")
                if file_size:
                    pyfile.size = file_size
                file_name = api_data["data"].get("name")
                if file_name:
                    pyfile.name = file_name

                progress = api_data["data"].get("progress", 0) * 100
                pyfile.set_progress(progress)
                if api_data["data"].get("download_state") == "completed":
                    break

                self.sleep(5)

            pyfile.set_progress(100)

        api_data = self.api_request("webdl/requestdl",
                                    api_key=api_key,
                                    get={
                                        "web_id": file_id,
                                        "zip": False,
                                        "token": api_key
                                    })
        if api_data.get("success", False):
            self.link = api_data["data"]

        else:
            self.fail(api_data["detail"])

    def check_errors(self, data=None):
        if isinstance(data, dict):
            if not data.get("success", False):
                error_code = data.get("error")
                if error_code == "DOWNLOAD_SERVER_ERROR":
                    self.offline()

                elif error_code == "DOWNLOAD_LIMIT_REACHED":
                    self.retry(5, 6*60, data["detail"])

                else:
                    self.log_error(data["detail"])
                    self.fail(data["detail"])
