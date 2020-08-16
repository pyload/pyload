# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class NetfolderIn(DeadDecrypter):
    __name__ = "NetfolderIn"
    __type__ = "decrypter"
    __version__ = "0.78"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?netfolder\.(in|me)/(folder\.php\?folder_id=)?(?P<ID>\w+)(?(1)|/\w+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """NetFolder.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("fragonib", "fragonib[AT]yahoo[DOT]es"),
    ]
