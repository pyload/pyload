# -*- coding: utf-8 -*-

import json
import re
import time
import urllib.parse

import pycurl

from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_downloader import MultiDownloader


class TorboxApp(MultiDownloader):
    __name__ = "TorboxApp"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https://store-\d+\.wnam\.tb-cdn\.io/dld/.*|(?P<APIURL>https://api\.torbox\.app/v1/api/(?P<ENDPOINT>webdl|torrents)/requestdl\?.*redirect=true.*)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Torbox.app multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    # See https://api-docs.torbox.app/
    API_URL = "https://api.torbox.app/v1/api/"

    def api_request(self, method, api_key=None, get=None, post=None):
        if api_key is not None:
            self.req.http.set_header("Authorization", f"Bearer {api_key}")

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

    def grab_info(self):
        super().grab_info()
        m = re.match(self.__pattern__, self.pyfile.url)
        if m is not None:
            api_url = m.group("APIURL")
            if api_url is not None:
                url_p = urllib.parse.urlparse(api_url)
                parse_qs = urllib.parse.parse_qs(url_p.query)
                endpoint = m.group("ENDPOINT")
                api_data = self.api_request(f"{endpoint}/mylist",
                                            api_key=parse_qs["token"][0],
                                            get={
                                                "id": parse_qs["web_id" if endpoint == "webdl" else "torrent_id"][0]
                                            })

                if api_data.get("success", False) and api_data.get("data"):
                    file_id = int(parse_qs["file_id"][0])
                    for file in api_data["data"]["files"]:
                        if file["id"] == file_id:
                            self.pyfile.name = file["short_name"]
                            self.pyfile.size = file["size"]
                            break

    def handle_direct(self, pyfile):
        link = self.isresource(pyfile.url)
        if link:
            self.link = pyfile.url

        else:
            self.link = None

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
                self.check_errors(api_data)

                file_size = api_data["data"].get("size")
                if file_size:
                    pyfile.size = file_size
                file_name = api_data["data"].get("name")
                if file_name:
                    pyfile.name = file_name

                progress = int(api_data["data"].get("progress", 0) * 100)
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
        self.check_errors(api_data)

        self.link = api_data["data"]

    def check_errors(self, data=None):
        if isinstance(data, dict):
            if not data.get("success", False):
                error_code = data.get("error")
                if error_code == "DOWNLOAD_SERVER_ERROR":
                    self.offline()

                elif error_code == "DOWNLOAD_LIMIT_REACHED":
                    self.log_error(data["detail"])
                    self.temp_offline()

                else:
                    self.log_error(data["detail"])
                    self.fail(data["detail"])
