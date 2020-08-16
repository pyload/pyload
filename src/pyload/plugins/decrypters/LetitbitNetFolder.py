# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class LetitbitNetFolder(DeadDecrypter):
    __name__ = "LetitbitNet"
    __type__ = "decrypter"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?letitbit\.net/folder/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Letitbit.net folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("DHMH", "webmaster@pcProfil.de"), ("z00nx", "z00nx0@gmail.com")]
