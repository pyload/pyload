# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class CryptItCom(DeadCrypter):
    __name    = "CryptItCom"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?crypt-it\.com/(s|e|d|c)/\w+'
    __config  = []

    __description = """Crypt-it.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("jeix", "jeix@hasnomail.de")]


getInfo = create_getInfo(CryptItCom)
