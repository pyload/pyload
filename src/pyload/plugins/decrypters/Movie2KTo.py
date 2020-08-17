# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class Movie2KTo(DeadDecrypter):
    __name__ = "Movie2KTo"
    __type__ = "decrypter"
    __version__ = "0.56"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?movie2k\.to/(.+)\.html"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Movie2k.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("4Christopher", "4Christopher@gmx.de")]
