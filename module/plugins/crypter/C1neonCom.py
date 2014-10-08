# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class C1neonCom(DeadCrypter):
    __name__ = "C1neonCom"
    __type__ = "crypter"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?c1neon.com/.*?'

    __description__ = """C1neon.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
