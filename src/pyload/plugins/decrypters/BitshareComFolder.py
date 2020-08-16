# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class BitshareComFolder(DeadDecrypter):
    __name__ = "BitshareComFolder"
    __type__ = "decrypter"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?bitshare\.com/\?d=\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Bitshare.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
