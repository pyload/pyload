# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class RSLayerCom(DeadDecrypter):
    __name__ = "RSLayerCom"
    __type__ = "decrypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?rs-layer\.com/directory-"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """RS-Layer.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
