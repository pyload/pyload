# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class SharingmatrixCom(DeadCrypter):
    __name__    = "SharingmatrixCom"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?sharingmatrix\.com/folder/\w+'

    __description__ = """Sharingmatrix.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(SharingmatrixCom)
