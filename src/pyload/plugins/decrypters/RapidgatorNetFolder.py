# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class RapidgatorNetFolder(SimpleDecrypter):
    __name__ = "RapidgatorNetFolder"
    __type__ = "decrypter"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:rapidgator\.(?:net|asia|)|rg\.to)/folder/(?P<ID>\w+)"
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

    __description__ = """Rapidgator.net folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaCode", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"<strong>\s*Downloading:\s*</strong>\s*(?P<N>.+?)\s+<"
    LINK_PATTERN = r'href="(/file/[^"]+)'
