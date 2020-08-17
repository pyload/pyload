# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class SecuredIn(DeadDecrypter):
    __name__ = "SecuredIn"
    __type__ = "decrypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?secured\.in/download-[\d]+\-\w{8}\.html"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Secured.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
