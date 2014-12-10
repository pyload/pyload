# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class StealthTo(DeadCrypter):
    __name    = "StealthTo"
    __type    = "crypter"
    __version = "0.20"

    __pattern = r'http://(?:www\.)?stealth\.to/folder/.+'
    __config  = []

    __description = """Stealth.to decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("spoob", "spoob@pyload.org")]


getInfo = create_getInfo(StealthTo)
