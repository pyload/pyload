# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class ILoadTo(DeadDecrypter):
    __name__ = "ILoadTo"
    __type__ = "decrypter"
    __version__ = "0.16"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?iload\.to/go/\d+\-[\w\-.]+/"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Iload.to decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("hzpz", None)]
