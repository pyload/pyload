# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class TrailerzoneInfo(DeadCrypter):
    __name__ = "TrailerzoneInfo"
    __type__ = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?trailerzone.info/.*?'

    __description__ = """TrailerZone.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
