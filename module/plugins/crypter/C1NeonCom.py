# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class C1NeonCom(DeadCrypter):
    __name__ = "C1NeonCom"
    __type__ = "crypter"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?c1neon\.com/.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """C1neon.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
