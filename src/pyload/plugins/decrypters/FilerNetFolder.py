# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class FilerNetFolder(SimpleDecrypter):
    __name__ = "FilerNetFolder"
    __type__ = "decrypter"
    __version__ = "0.48"
    __status__ = "testing"

    __pattern__ = r"https?://filer\.net/folder/\w{16}"
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
    ]

    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'

    NAME_PATTERN = r"<h3>(?P<N>.+?) - <small"
    OFFLINE_PATTERN = r"Nicht gefunden"
