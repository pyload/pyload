# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class StealthTo(DeadCrypter):
    __name    = "StealthTo"
    __type    = "crypter"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?stealth\.to/folder/.+'
    __config  = []

    __description = """Stealth.to decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org")]
