# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class TrailerzoneInfo(DeadDecrypter):
    __name__ = "TrailerzoneInfo"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?trailerzone\.info/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """TrailerZone.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
