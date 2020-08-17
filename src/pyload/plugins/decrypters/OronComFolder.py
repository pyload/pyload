# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class OronComFolder(DeadDecrypter):
    __name__ = "OronComFolder"
    __type__ = "decrypter"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?oron\.com/folder/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Oron.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("DHMH", "webmaster@pcProfil.de")]
