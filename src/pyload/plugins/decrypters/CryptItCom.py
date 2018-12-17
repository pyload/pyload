# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class CryptItCom(DeadDecrypter):
    __name__ = "CryptItCom"
    __type__ = "decrypter"
    __version__ = "0.16"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?crypt-it\.com/(s|e|d|c)/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Crypt-it.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de")]
