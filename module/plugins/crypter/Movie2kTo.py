# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class Movie2kTo(DeadCrypter):
    __name__ = "Movie2kTo"
    __type__ = "crypter"
    __version__ = "0.51"

    __pattern__ = r'http://(?:www\.)?movie2k\.to/(.*)\.html'

    __description__ = """Movie2k.to decrypter plugin"""
    __author_name__ = "4Christopher"
    __author_mail__ = "4Christopher@gmx.de"
