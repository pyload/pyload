# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class C1NeonCom(DeadCrypter):
    __name__    = "C1NeonCom"
    __type__    = "crypter"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?c1neon\.com/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """C1neon.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com")]


getInfo = create_getInfo(C1NeonCom)
