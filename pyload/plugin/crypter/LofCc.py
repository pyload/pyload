# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class LofCc(DeadCrypter):
    __name    = "LofCc"
    __type    = "crypter"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?lof\.cc/(.+)'
    __config  = []

    __description = """Lof.cc decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]
