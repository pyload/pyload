# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class StealthTo(DeadCrypter):
    __name__    = "StealthTo"
    __type__    = "crypter"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?stealth\.to/folder/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Stealth.to decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org")]


getInfo = create_getInfo(StealthTo)
