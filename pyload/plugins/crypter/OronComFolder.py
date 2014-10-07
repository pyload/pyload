# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter


class OronComFolder(DeadCrypter):
    __name__ = "OronComFolder"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?oron.com/folder/\w+'

    __description__ = """Oron.com folder decrypter plugin"""
    __authors__ = [("DHMH", "webmaster@pcProfil.de")]
