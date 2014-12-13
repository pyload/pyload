# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class ILoadTo(DeadCrypter):
    __name    = "ILoadTo"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?iload\.to/go/\d+-[\w.-]+/'
    __config  = []

    __description = """Iload.to decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("hzpz", "")]


getInfo = create_getInfo(ILoadTo)
