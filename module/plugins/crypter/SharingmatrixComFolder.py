# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class SharingmatrixComFolder(DeadCrypter):
    __name__ = "SharingmatrixComFolder"
    __type__ = "crypter"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?sharingmatrix\.com/folder/\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Sharingmatrix.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
