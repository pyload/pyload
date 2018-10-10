# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class Movie2KTo(DeadCrypter):
    __name__ = "Movie2KTo"
    __type__ = "crypter"
    __version__ = "0.56"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?movie2k\.to/(.+)\.html'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Movie2k.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("4Christopher", "4Christopher@gmx.de")]
