# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadcrypter import DeadCrypter


class MBLinkInfo(DeadCrypter):
    __name__ = "MBLinkInfo"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?mblink\.info/?\?id=(\d+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """MBLink.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Gummibaer", "Gummibaer@wiki-bierkiste.de"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
