# -*- coding: utf-8 -*

import json

from pyload.core.network.http.exceptions import BadHeader

from ..base.decrypter import BaseDecrypter


class GoogledriveComDereferer(BaseDecrypter):
    __name__ = "GoogledriveComDereferer"
    __type__ = "decrypter"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:drive|docs)\.google\.com/open\?(?:.+;)?id=(?P<ID>[-\w]+)"
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

    __description__ = """Drive.google.com dereferer plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r"folderName: '(?P<N>.+?)'"
    OFFLINE_PATTERN = r"<TITLE>"

    API_URL = "https://www.googleapis.com/drive/v3/"
    API_KEY = "AIzaSyB68u-qFPP9oBJpo1DWAPFE_VD2Sfy9hpk"

    def api_request(self, cmd, **kwargs):
        kwargs["key"] = self.API_KEY
        try:
            json_data = json.loads(
                self.load("{}{}".format(self.API_URL, cmd), get=kwargs)
            )
            self.log_debug(f"API response: {json_data}")
            return json_data

        except BadHeader as exc:
            try:
                json_data = json.loads(exc.content)
                self.log_error(
                    "API Error: {}".format(cmd),
                    json_data["error"]["message"],
                    "ID: {}".format(self.info["pattern"]["ID"]),
                    "Error code: {}".format(exc.code),
                )

            except ValueError:
                self.log_error(
                    "API Error: {}".format(cmd),
                    exc,
                    "ID: {}".format(self.info["pattern"]["ID"]),
                    "Error code: {}".format(exc.code),
                )
            return None

    def decrypt(self, pyfile):
        json_data = self.api_request("files/{}".format(self.info["pattern"]["ID"]))
        if json_data is None:
            self.fail("API error")

        if "error" in json_data:
            if json_data["error"]["code"] == 404:
                self.offline()

            else:
                self.fail(json_data["error"]["message"])

        link = "https://drive.google.com/{}/{}".format(
            (
                "file/d"
                if json_data["mimeType"] != "application/vnd.google-apps.folder"
                else "drive/folders"
            ),
            self.info["pattern"]["ID"],
        )

        self.packages = [(pyfile.package().folder, [link], pyfile.package().name)]
