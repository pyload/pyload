# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class LofCc(DeadCrypter):
    __name    = "LofCc"
    __type    = "crypter"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?lof\.cc/(.*)'
    __config  = []

    __description = """Lof.cc decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(LofCc)
