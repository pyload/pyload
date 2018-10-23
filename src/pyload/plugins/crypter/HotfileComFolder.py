# -*- coding: utf-8 -*-

from ..internal.deadcrypter import DeadCrypter


class HotfileComFolder(DeadCrypter):
    __name__ = "HotfileComFolder"
    __type__ = "crypter"
    __version__ = "0.36"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"https?://(?:www\.)?hotfile\.com/list/\w+/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Hotfile.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]
