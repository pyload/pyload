# -*- coding: utf-8 -*-
import base64
import json
import re
import urllib.parse

from ..base.decrypter import BaseDecrypter


class CloudMailRuFolder(BaseDecrypter):
    __name__ = "CloudMailRuFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://cloud\.mail\.ru/public/.+"
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

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)

        m = re.search(r"window\.cloudSettings\s*=\s*({{.+?}});", self.data, re.S)
        if m is None:
            self.fail(self._("Json pattern not found"))

        json_data = json.loads(m.group(1).replace("\\x3c", "<"))

        pack_links = [
            "https://cloud.mail.ru/dl?q={}".format(
                base64.b64encode(
                    json.dumps(
                        {
                            "u": "{}{}?etag={}&key={}".format(
                                json_data["dispatcher"]["weblink_view"][0]["url"],
                                urllib.parse.quote(link["weblink"]),
                                link["hash"],
                                json_data["params"]["tokens"]["download"],
                            ),
                            "n": urllib.parse.quote_plus(link["name"]),
                            "s": link["size"],
                        }
                    )
                )
            )
            for link in json_data["folders"]["folder"]["list"]
            if link["kind"] == "file"
        ]

        if pack_links:
            self.packages.append(
                (pyfile.package().name, pack_links, pyfile.package().folder)
            )
