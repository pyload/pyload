# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class CrockoComFolder(SimpleDecrypter):
    __name__ = "CrockoComFolder"
    __type__ = "decrypter"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?crocko\.com/f/.+"
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

    __description__ = """Crocko.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    LINK_PATTERN = r'<td class="last"><a href="(.+?)">download</a>'
