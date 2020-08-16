# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class DdlstorageComFolder(DeadDecrypter):
    __name__ = "DdlstorageComFolder"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?ddlstorage\.com/folder/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """DDLStorage.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("godofdream", "soilfiction@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
    ]
