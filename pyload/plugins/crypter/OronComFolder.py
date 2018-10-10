# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class OronComFolder(DeadCrypter):
    __name__ = "OronComFolder"
    __type__ = "crypter"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?oron\.com/folder/\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Oron.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("DHMH", "webmaster@pcProfil.de")]
