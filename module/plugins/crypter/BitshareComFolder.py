# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class BitshareComFolder(DeadCrypter):
    __name__    = "BitshareComFolder"
    __type__    = "crypter"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/\?d=\w+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Bitshare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]
