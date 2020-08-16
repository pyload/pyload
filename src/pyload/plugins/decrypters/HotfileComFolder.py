# -*- coding: utf-8 -*-

from ..base.dead_decrypter import DeadDecrypter


class HotfileComFolder(DeadDecrypter):
    __name__ = "HotfileComFolder"
    __type__ = "decrypter"
    __version__ = "0.36"
    __status__ = "stable"

    __pattern__ = r"https?://(?:www\.)?hotfile\.com/list/\w+/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Hotfile.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]
