# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter


class SpeedLoadOrgFolder(DeadCrypter):
    __name__ = "SpeedLoadOrgFolder"
    __type__ = "crypter"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(\d+~f$|folder/\d+/)'

    __description__ = """Speedload decrypter plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
