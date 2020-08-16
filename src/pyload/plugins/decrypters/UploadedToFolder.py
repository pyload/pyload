# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class UploadedToFolder(SimpleDecrypter):
    __name__ = "UploadedToFolder"
    __type__ = "decrypter"
    __version__ = "0.49"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/\w+"
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

    __description__ = """UploadedTo decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    NAME_PATTERN = r"<title>(?P<N>.+?)<"
    OFFLINE_PATTERN = r">Page not found"
    TEMP_OFFLINE_PATTERN = r"<title>uploaded\.net - Maintenance"

    LINK_PATTERN = r'<h2><a href="(.+?)"'
