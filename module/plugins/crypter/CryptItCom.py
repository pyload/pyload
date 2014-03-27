# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class CryptItCom(DeadCrypter):
    __name__ = "CryptItCom"
    __type__ = "container"
    __pattern__ = r"http://[\w\.]*?crypt-it\.com/(s|e|d|c)/[\w]+"
    __version__ = "0.11"
    __description__ = """Crypt-it.com decrypter plugin"""
    __author_name__ = "jeix"
    __author_mail__ = "jeix@hasnomail.de"
