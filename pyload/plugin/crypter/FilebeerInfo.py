# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class FilebeerInfo(DeadCrypter):
    __name    = "FilebeerInfo"
    __type    = "crypter"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?filebeer\.info/\d*~f\w+'
    __config  = []

    __description = """Filebeer.info folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
