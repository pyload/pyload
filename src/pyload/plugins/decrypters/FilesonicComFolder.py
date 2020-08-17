# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class FilesonicComFolder(DeadDecrypter):
    __name__ = "FilesonicComFolder"
    __type__ = "decrypter"
    __version__ = "0.18"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filesonic\.com/folder/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Filesonic.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
