# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class OronComFolder(DeadCrypter):
    __name__    = "OronComFolder"
    __type__    = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?oron\.com/folder/\w+'
    __config__  = []

    __description__ = """Oron.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("DHMH", "webmaster@pcProfil.de")]


getInfo = create_getInfo(OronComFolder)
