# -*- coding: utf-8 -*-

import json

from ..base.decrypter import BaseDecrypter


class MediafireComFolder(BaseDecrypter):
    __name__ = "MediafireComFolder"
    __type__ = "decrypter"
    __version__ = "0.25"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?mediafire\.com/(?:folder/|\?sharekey=|\?)(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Mediafire.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See http://www.mediafire.com/developers/core_api/
    API_URL = "http://www.mediafire.com/api/"

    def api_request(self, method, **kwargs):
        kwargs["response_format"] = "json"
        json_data = self.load(self.API_URL + method + ".php", get=kwargs)
        res = json.loads(json_data)

        if res["response"]["result"] != "Success":
            self.fail(res["response"]["message"])

        return res

    def decrypt(self, pyfile):
        api_data = self.api_request(
            "folder/get_info", folder_key=self.info["pattern"]["ID"]
        )
        pack_name = (
            api_data["response"]["folder_info"].get("name")
            or self.pyfile.package().name
        )

        api_data = self.api_request(
            "folder/get_content",
            folder_key=self.info["pattern"]["ID"],
            content_type="files",
        )
        pack_links = [
            "http://www.mediafire.com/file/{}".format(f["quickkey"])
            for f in api_data["response"]["folder_content"]["files"]
        ]

        if pack_links:
            self.packages.append((pack_name, pack_links, pack_name))
