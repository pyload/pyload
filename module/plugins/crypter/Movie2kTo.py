# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class Movie2kTo(DeadCrypter):
    __name__ = "Movie2kTo"
    __type__ = "crypter"
    __version__ = "0.51"

    __pattern__ = r'http://(?:www\.)?movie2k\.to/(.*)\.html'
    __config__  = []

    __description__ = """Movie2k.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("4Christopher", "4Christopher@gmx.de")]
