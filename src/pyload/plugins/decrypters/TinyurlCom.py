# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class TinyurlCom(SimpleDecrypter):
    __name__ = "TinyurlCom"
    __type__ = "decrypter"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(preview\.)?tinyurl\.com/[\w\-]+"
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

    __description__ = """Tinyurl.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [(r"preview\.", r"")]

    OFFLINE_PATTERN = r">Error: Unable to find site's URL to redirect to"
