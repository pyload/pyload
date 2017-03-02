# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class RSLayerCom(DeadCrypter):
    __name__ = "RSLayerCom"
    __type__ = "crypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?rs-layer\.com/directory-'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """RS-Layer.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
