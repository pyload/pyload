# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class SpeedLoadOrgFolder(DeadCrypter):
    __name__ = "SpeedLoadOrgFolder"
    __type__ = "crypter"
    __version__ = "0.36"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(\d+~f$|folder/\d+/)'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Speedload decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
