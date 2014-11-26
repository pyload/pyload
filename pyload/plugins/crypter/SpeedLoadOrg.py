# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class SpeedLoadOrg(DeadCrypter):
    __name__    = "SpeedLoadOrg"
    __type__    = "crypter"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(\d+~f$|folder/\d+/)'
    __config__  = []

    __description__ = """Speedload decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(SpeedLoadOrg)
