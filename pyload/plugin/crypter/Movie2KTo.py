# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class Movie2KTo(DeadCrypter):
    __name    = "Movie2KTo"
    __type    = "crypter"
    __version = "0.51"

    __pattern = r'http://(?:www\.)?movie2k\.to/(.+)\.html'
    __config  = []

    __description = """Movie2k.to decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("4Christopher", "4Christopher@gmx.de")]
