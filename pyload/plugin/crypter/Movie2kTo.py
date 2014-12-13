# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class Movie2kTo(DeadCrypter):
    __name    = "Movie2kTo"
    __type    = "crypter"
    __version = "0.51"

    __pattern = r'http://(?:www\.)?movie2k\.to/(.*)\.html'
    __config  = []

    __description = """Movie2k.to decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("4Christopher", "4Christopher@gmx.de")]


getInfo = create_getInfo(Movie2kTo)
