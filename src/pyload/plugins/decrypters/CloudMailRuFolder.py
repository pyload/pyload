# -*- coding: utf-8 -*-

import base64
import json

from ..base.decrypter import BaseDecrypter


class CloudMailRuFolder(BaseDecrypter):
    __name__ = "CloudMailRuFolder"
    __type__ = "decrypter"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://cloud\.mail\.ru/public/(?P<ID>.+)"
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
    ]

    __description__ = """Cloud.mail.ru decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://cloud.mail.ru/api/v2/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def decrypt(self, pyfile):
        api_data = self.api_request("dispatcher", api=2)
        if api_data["status"] != 200:
            self.fail(self._("API failure, status code {}").format(api_data["status"]))

        base_url = api_data["body"]["weblink_get"][0]["url"]

        api_data = self.api_request(
            "folder", weblink=self.info["pattern"]["ID"], offset=0, limit=500, api=2
        )

        if api_data["status"] != 200:
            self.fail(self._("API failure, status code {}").format(api_data["status"]))

        pack_name = api_data["body"]["name"]
        pack_links = [
            "https://cloud.mail.ru/dl?q={}".format(
                base64.b64encode(
                    json.dumps(
                        {
                            "u": "{}/{}".format(base_url, _link["weblink"]),
                            "n": _link["name"],
                            "s": _link["size"],
                        }
                    ).encode("utf-8")
                ).decode("utf-8")
            )
            for _link in api_data["body"]["list"]
            if _link["type"] == "file"
        ]

        if pack_links:
            self.packages.append(
                (
                    pack_name or pyfile.package().name,
                    pack_links,
                    pack_name or pyfile.package().folder,
                )
            )
