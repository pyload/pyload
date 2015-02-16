# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class DdlstorageCom(DeadCrypter):
    __name__    = "DdlstorageCom"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/folder/\w+'
    __config__  = []

    __description__ = """DDLStorage.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]
