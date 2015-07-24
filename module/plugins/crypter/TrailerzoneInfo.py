# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class TrailerzoneInfo(DeadCrypter):
    __name__    = "TrailerzoneInfo"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?trailerzone\.info/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """TrailerZone.info decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com")]


getInfo = create_getInfo(TrailerzoneInfo)
