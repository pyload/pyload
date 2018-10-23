# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadcrypter import DeadCrypter


class SecuredIn(DeadCrypter):
    __name__ = "SecuredIn"
    __type__ = "crypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?secured\.in/download-[\d]+\-\w{8}\.html"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Secured.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de")]
