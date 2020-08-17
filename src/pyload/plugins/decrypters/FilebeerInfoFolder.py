# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class FilebeerInfoFolder(DeadDecrypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filebeer\.info/\d*~f\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Filebeer.info folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
