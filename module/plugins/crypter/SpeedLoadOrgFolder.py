# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class SpeedLoadOrgFolder(DeadCrypter):
    __name__    = "SpeedLoadOrgFolder"
    __type__    = "crypter"
    __version__ = "0.31"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(\d+~f$|folder/\d+/)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Speedload decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(SpeedLoadOrgFolder)
