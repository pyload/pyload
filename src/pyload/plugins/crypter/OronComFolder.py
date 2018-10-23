# -*- coding: utf-8 -*-

from ..internal.deadcrypter import DeadCrypter


class OronComFolder(DeadCrypter):
    __name__ = "OronComFolder"
    __type__ = "crypter"
    __version__ = "0.17"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?oron\.com/folder/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Oron.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("DHMH", "webmaster@pcProfil.de")]
