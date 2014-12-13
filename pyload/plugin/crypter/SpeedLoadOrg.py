# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class SpeedLoadOrg(DeadCrypter):
    __name    = "SpeedLoadOrg"
    __type    = "crypter"
    __version = "0.30"

    __pattern = r'http://(?:www\.)?speedload\.org/(\d+~f$|folder/\d+/)'
    __config  = []

    __description = """Speedload decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(SpeedLoadOrg)
