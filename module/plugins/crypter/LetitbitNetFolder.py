# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class LetitbitNetFolder(DeadCrypter):
    __name__ = "LetitbitNet"
    __type__ = "crypter"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?letitbit\.net/folder/\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Letitbit.net folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("DHMH", "webmaster@pcProfil.de"),
                   ("z00nx", "z00nx0@gmail.com")]
