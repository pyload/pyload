# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class DuploadOrgFolder(DeadDecrypter):
    __name__ = "DuploadOrgFolder"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?dupload\.org/folder/\d+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Dupload.org folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
