# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class ILoadTo(DeadCrypter):
    __name__    = "ILoadTo"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?iload\.to/go/\d+-[\w.-]+/'
    __config__  = []

    __description__ = """Iload.to decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("hzpz", "")]


getInfo = create_getInfo(ILoadTo)
