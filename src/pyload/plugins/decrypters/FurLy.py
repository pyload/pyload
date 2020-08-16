# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class FurLy(SimpleDecrypter):
    __name__ = "FurLy"
    __type__ = "decrypter"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?fur\.ly/(\d/)?\w+"
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

    __description__ = """Fur.ly decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = [(r"fur\.ly/", r"fur\.ly/bar/")]

    LINK_PATTERN = r'urls\[\d+\] = "(.+?)"'
    OFFLINE_PATTERN = r"var output;\s*var total"
