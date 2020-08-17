# -*- coding: utf-8 -*-

import json

from ..base.simple_decrypter import SimpleDecrypter


class GooGl(SimpleDecrypter):
    __name__ = "GooGl"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?goo\.gl/([a-zA-Z]+/)?\w+"
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

    __description__ = """Goo.gl decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    API_URL = "https://www.googleapis.com/urlshortener/v1/url"

    OFFLINE_PATTERN = r"has been disabled|does not exist"

    def get_links(self):
        rep = self.load(self.API_URL, get={"shortUrl": self.pyfile.url})
        self.log_debug("JSON data: " + rep)
        rep = json.loads(rep)
        return [rep["longUrl"]] if "longUrl" in rep else None
