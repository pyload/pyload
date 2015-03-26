# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class C1NeonCom(DeadCrypter):
    __name    = "C1NeonCom"
    __type    = "crypter"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?c1neon\.com/.+'
    __config  = []

    __description = """C1neon.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]
