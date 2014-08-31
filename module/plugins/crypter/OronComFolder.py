# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class OronComFolder(DeadCrypter):
    __name__ = "OronComFolder"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?oron.com/folder/\w+'

    __description__ = """Oron.com folder decrypter plugin"""
    __author_name__ = "DHMH"
    __author_mail__ = "webmaster@pcProfil.de"
