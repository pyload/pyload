# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class ILoadTo(DeadCrypter):
    __name__ = "ILoadTo"
    __type__ = "crypter"
    __version__ = "0.16"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?iload\.to/go/\d+\-[\w\-.]+/'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Iload.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
