# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class OronComFolder(DeadCrypter):
    __name__    = "OronComFolder"
    __type__    = "crypter"
    __version__ = "0.14"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?oron\.com/folder/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Oron.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("DHMH", "webmaster@pcProfil.de")]


getInfo = create_getInfo(OronComFolder)
