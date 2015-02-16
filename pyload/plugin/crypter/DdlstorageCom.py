# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class DdlstorageCom(DeadCrypter):
    __name    = "DdlstorageCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?ddlstorage\.com/folder/\w+'
    __config  = []

    __description = """DDLStorage.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]
