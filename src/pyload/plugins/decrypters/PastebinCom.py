# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class PastebinCom(SimpleDecrypter):
    __name__ = "PastebinCom"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"https://(?:www\.)?pastebin\.com/(.+i=)?(?P<ID>\w{8})"
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

    __description__ = """Pastebin.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"http://www.pastebin.com/\g<ID>")]

    NAME_PATTERN = r'<div class="paste_box_line1" title="(?P<N>.+?)"'
    LINK_PATTERN = r'<div class="de\d+">(.+?)<'
