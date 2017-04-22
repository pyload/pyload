# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class DuploadOrgFolder(DeadCrypter):
    __name__ = "DuploadOrgFolder"
    __type__ = "crypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?dupload\.org/folder/\d+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Dupload.org folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
