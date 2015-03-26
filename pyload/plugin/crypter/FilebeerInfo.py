# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class FilebeerInfo(DeadCrypter):
    __name__    = "FilebeerInfo"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?filebeer\.info/\d*~f\w+'
    __config__  = []

    __description__ = """Filebeer.info folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
