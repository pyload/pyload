# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class OronComFolder(DeadCrypter):
    __name__    = "OronComFolder"
    __type__    = "crypter"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?oron\.com/folder/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Oron.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("DHMH", "webmaster@pcProfil.de")]


getInfo = create_getInfo(OronComFolder)
