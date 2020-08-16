# -*- coding: utf-8 -*-

import json
import re

import pycurl

from ..base.decrypter import BaseDecrypter
from ..helpers import replace_patterns


class FshareVnFolder(BaseDecrypter):
    __name__ = "FshareVnFolder"
    __type__ = "decrypter"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?fshare\.vn/folder/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("dl_subfolders", "bool", "Download subfolders", False),
        ("package_subfolder", "bool", "Subfolder as a separate package", False),
    ]

    __description__ = """Fshare.vn folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    OFFLINE_PATTERN = r"Thư mục của bạn yêu cầu không tồn tại"
    NAME_PATTERN = r"<title>Fshare - (.+?)(?: - Fshare)?</title>"

    URL_REPLACEMENTS = [("http://", "https://")]

    def enum_folder(self, folder_id):
        links = []

        self.req.http.c.setopt(
            pycurl.HTTPHEADER, ["Accept: application/json, text/plain, */*"]
        )
        self.data = self.load(
            "https://www.fshare.vn/api/v3/files/folder", get={"linkcode": folder_id}
        )
        json_data = json.loads(self.data)

        current_page = 1
        last_page = int(
            re.search(r"&page=(\d+)", json_data["_links"].get("last", "&page=1")).group(
                1
            )
        )

        while True:
            folder_items = json_data["items"]
            for item in folder_items:
                if item["type"] == 1:
                    links.append("https://www.fshare.vn/file/" + item["linkcode"])

                else:
                    if self.config.get("dl_subfolders"):
                        if self.config.get("package_subfolder"):
                            links.append(
                                "https://www.fshare.vn/folder/" + item["linkcode"]
                            )

                        else:
                            links.extend(self.enum_folder(item["linkcode"]))

            current_page += 1
            if current_page > last_page:
                break

            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Accept: application/json, text/plain, */*"]
            )
            self.data = self.load(
                "https://www.fshare.vn/api/v3/files/folder",
                get={"linkcode": folder_id, "page": current_page},
            )
            json_data = json.loads(self.data)

        return links

    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        self.data = self.load(pyfile.url)
        if re.search(self.OFFLINE_PATTERN, self.data):
            self.offline()

        m = re.search(self.NAME_PATTERN, self.data)
        pack_name = m.group(1) if m is not None else pyfile.package().name

        links = self.enum_folder(self.info["pattern"]["ID"])

        if links:
            self.packages = [(pack_name, links, pack_name)]
