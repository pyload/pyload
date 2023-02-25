# -*- coding: utf-8 -*-

import base64
import json

from ..base.decrypter import BaseDecrypter


class GofileIoFolder(BaseDecrypter):
    __name__ = "GofileIoFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?gofile\.io/d/(?P<ID>\w+)"
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

    __description__ = """Gofile.io decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [("http://", "https://")]

    API_URL = "https://api.gofile.io/"

    def api_request(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def decrypt(self, pyfile):
        api_data = self.api_request("createAccount")
        if api_data["status"] != "ok":
            self.fail(
                self._("createAccount API failed | {}").format(api_data["status"])
            )

        token = api_data["data"]["token"]
        api_data = self.api_request(
            "getContent",
            contentId=self.info["pattern"]["ID"],
            token=token,
            websiteToken=12345,
        )
        status = api_data["status"]
        if status == "ok":
            pack_links = [
                "https://gofile.io/dl?q={}".format(
                    base64.b64encode(
                        json.dumps(
                            {
                                "t": token,
                                "u": file_data["link"],
                                "n": file_data["name"],
                                "s": file_data["size"],
                                "m": file_data["md5"],
                            }
                        ).encode("utf-8")
                    ).decode("utf-8")
                )
                for file_data in api_data["data"]["contents"].values()
                if file_data["type"] == "file"
            ]

            if pack_links:
                self.packages.append(
                    (pyfile.package().name, pack_links, pyfile.package().folder)
                )

            else:
                self.offline()

        elif status == "error-notFound":
            self.offline()

        else:
            self.fail("getContent API failed | {}".format(status))
