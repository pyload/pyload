# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class OronCom(DeadCrypter):
    __name    = "OronCom"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?oron\.com/folder/\w+'
    __config  = []

    __description = """Oron.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("DHMH", "webmaster@pcProfil.de")]
