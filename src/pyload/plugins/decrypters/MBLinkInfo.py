# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class MBLinkInfo(DeadDecrypter):
    __name__ = "MBLinkInfo"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?mblink\.info/?\?id=(\d+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """MBLink.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
