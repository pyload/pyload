# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class ILoadTo(DeadCrypter):
    __name__    = "ILoadTo"
    __type__    = "crypter"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?iload\.to/go/\d+-[\w.-]+/'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Iload.to decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("hzpz", None)]


getInfo = create_getInfo(ILoadTo)
