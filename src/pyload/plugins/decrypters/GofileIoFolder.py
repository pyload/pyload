# -*- coding: utf-8 -*-

import base64
import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.decrypter import BaseDecrypter


class GofileIoFolder(BaseDecrypter):
    __name__ = "GofileIoFolder"
    __type__ = "decrypter"
    __version__ = "0.03"
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

    def api_request(self, method, token=None, get={}, post={}):
        if token is not None:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + token]
            )
        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def decrypt(self, pyfile):
        api_data = self.api_request("accounts", post=True)
        if api_data["status"] != "ok":
            self.fail(
                self._("accounts API failed | {}").format(api_data["status"])
            )

        token = api_data["data"]["token"]
        api_data = self.api_request(
            "contents/{}".format(self.info["pattern"]["ID"]),
            token=token,
            get={"wt": "4fd6sg89d7s6"}
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
                for file_data in api_data["data"]["children"].values()
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

        elif status == "error-notPremium":
            self.fail(self._("File can be downloaded by premium users only"))

        else:
            self.fail(self._("getContent API failed | {}").format(status))
