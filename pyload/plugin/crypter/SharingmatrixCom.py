# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter, create_getInfo


class SharingmatrixCom(DeadCrypter):
    __name    = "SharingmatrixCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sharingmatrix\.com/folder/\w+'

    __description = """Sharingmatrix.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(SharingmatrixCom)
