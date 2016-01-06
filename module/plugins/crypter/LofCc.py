# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class LofCc(DeadCrypter):
    __name__    = "LofCc"
    __type__    = "crypter"
    __version__ = "0.25"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?lof\.cc/(.+)'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Lof.cc decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]
