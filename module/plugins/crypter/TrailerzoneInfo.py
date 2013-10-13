# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class TrailerzoneInfo(DeadCrypter):
    __name__ = "TrailerzoneInfo"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?trailerzone.info/.*?"
    __version__ = "0.03"
    __description__ = """TrailerZone.info Crypter Plugin"""
    __author_name__ = ("godofdream")
    __author_mail__ = ("soilfiction@gmail.com")
