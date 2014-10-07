# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter


class StealthTo(DeadCrypter):
    __name__ = "StealthTo"
    __type__ = "crypter"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?stealth\.to/folder/.+'

    __description__ = """Stealth.to decrypter plugin"""
    __authors__ = [("spoob", "spoob@pyload.org")]
