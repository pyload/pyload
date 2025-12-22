# -*- coding: utf-8 -*-

import json

from pyload.core.network.http.exceptions import BadHeader

from ..base.decrypter import BaseDecrypter


class FilerNetFolder(BaseDecrypter):
    __name__ = "FilerNetFolder"
    __type__ = "decrypter"
    __version__ = "0.49"
    __status__ = "testing"

    __pattern__ = r"https?://filer\.net/folder/(?P<ID>\w+)"
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

    __description__ = """Filer.net decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("nath_schwarz", "nathan.notwhite@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def api_request(self, method, **kwargs):
        try:
            json_data = self.load(self.API_URL + method, post=kwargs)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def decrypt(self, pyfile):
        api_data = self.api_request(f"folder/{self.info['pattern']['ID']}")
        pack_name = api_data["name"]
        pack_links = [
            f"https://filer.net/get/{f['hash']}"
            for f in api_data["files"]
        ]
        if pack_links:
            self.packages.append(
                (
                    pack_name or pyfile.package().name,
                    pack_links,
                    pack_name or pyfile.package().folder,
                )
            )
