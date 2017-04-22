# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class FilebeerInfoFolder(DeadCrypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?filebeer\.info/\d*~f\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Filebeer.info folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
