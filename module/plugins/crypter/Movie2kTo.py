# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class Movie2kTo(DeadCrypter):
    __name__ = "Movie2kTo"
    __type__ = "container"
    __pattern__ = r"http://(?:www\.)?movie2k\.to/(.*)\.html"
    __version__ = "0.51"
    __description__ = """Movie2k.to Container Plugin"""
    __author_name__ = ("4Christopher")
    __author_mail__ = ("4Christopher@gmx.de")
