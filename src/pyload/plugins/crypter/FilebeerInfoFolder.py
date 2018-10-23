# -*- coding: utf-8 -*-

from ..internal.deadcrypter import DeadCrypter


class FilebeerInfoFolder(DeadCrypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?filebeer\.info/\d*~f\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Filebeer.info folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
