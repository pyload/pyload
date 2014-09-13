# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class StealthTo(DeadCrypter):
    __name__ = "StealthTo"
    __type__ = "crypter"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?stealth\.to/folder/.+'

    __description__ = """Stealth.to decrypter plugin"""
    __author_name__ = "spoob"
    __author_mail__ = "spoob@pyload.org"
