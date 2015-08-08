# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class DdlstorageComFolder(DeadCrypter):
    __name__    = "DdlstorageComFolder"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/folder/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """DDLStorage.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(DdlstorageComFolder)
