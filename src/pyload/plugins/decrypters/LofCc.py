# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class LofCc(DeadDecrypter):
    __name__ = "LofCc"
    __type__ = "decrypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?lof\.cc/(.+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Lof.cc decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
