# -*- coding: utf-8 -*-

import base64
import json
import re
import urllib.parse

from pyload.core.network.request_factory import get_url

from ..base.simple_decrypter import SimpleDecrypter


def xor_decrypt(data, key):
    data = base64.b64decode(data)
    return "".join(
        [
            chr(ord(x[1]) ^ ord(key[x[0].format(len(key))]))
            for x in [(i, c) for i, c in enumerate(data)]
        ]
    )


class MegadyskPlFolder(SimpleDecrypter):
    __name__ = "MegadyskPlFolder"
    __type__ = "decrypter"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?megadysk\.pl/(?:f|s)/.+"
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

    __description__ = """Megadysk.pl folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    @classmethod
    def api_info(cls, url):
        html = get_url(url)
        info = {}

        m = re.search(r"window\['.*?'\]\s*=\s*\"(.*?)\"", html)
        if m is None:
            info["status"] = 8
            info["error"] = "Encrypted info pattern not found"
            return info

        encrypted_info = m.group(1)

        html = get_url("https://megadysk.pl/dist/index.js")

        m = re.search(r't.ISK\s*=\s*"(\w+)"', html)
        if m is None:
            info["status"] = 8
            info["error"] = "Encryption key pattern not found"
            return info

        key = m.group(1)

        res = xor_decrypt(encrypted_info, key)
        json_data = json.loads(urllib.parse.unquote(res))

        if json_data["app"]["maintenance"]:
            info["status"] = 6
            return info

        if json_data["app"]["folderView"]["notFound"]:
            info["status"] = 1
            return info

        info["entities"] = json_data["app"]["folderView"]["entities"]

        return info

    def decrypt(self, pyfile):
        if "entities" not in self.info:
            self.error(self._("Missing JSON data"))

        pack_links = [
            self.fixurl(l["downloadUrl"])
            for l in self.info["entities"]
            if l["downloadUrl"].startswith("/dl/")
        ]

        if pack_links:
            self.packages.append(
                (pyfile.package().name, pack_links, pyfile.package().folder)
            )
