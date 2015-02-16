# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class SecuredIn(DeadCrypter):
    __name    = "SecuredIn"
    __type    = "crypter"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?secured\.in/download-[\d]+-\w{8}\.html'
    __config  = []

    __description = """Secured.in decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]
