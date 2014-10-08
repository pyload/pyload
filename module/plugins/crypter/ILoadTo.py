# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class ILoadTo(DeadCrypter):
    __name__ = "ILoadTo"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?iload\.to/go/\d+-[\w\.-]+/'

    __description__ = """Iload.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
