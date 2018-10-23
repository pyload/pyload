# -*- coding: utf-8 -*-

from ..internal.deadcrypter import DeadCrypter


class LofCc(DeadCrypter):
    __name__ = "LofCc"
    __type__ = "crypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?lof\.cc/(.+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Lof.cc decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
