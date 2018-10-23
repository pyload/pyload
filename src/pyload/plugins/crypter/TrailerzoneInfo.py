# -*- coding: utf-8 -*-

from ..internal.deadcrypter import DeadCrypter


class TrailerzoneInfo(DeadCrypter):
    __name__ = "TrailerzoneInfo"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?trailerzone\.info/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """TrailerZone.info decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
