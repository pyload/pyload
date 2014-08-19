# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class TrailerzoneInfo(DeadCrypter):
    __name__ = "TrailerzoneInfo"
    __version__ = "0.03"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?trailerzone.info/.*?'

    __description__ = """TrailerZone.info decrypter plugin"""
    __author_name__ = "godofdream"
    __author_mail__ = "soilfiction@gmail.com"
