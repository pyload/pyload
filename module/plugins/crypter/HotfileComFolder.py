# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class HotfileComFolder(DeadCrypter):
    __name__ = "HotfileComFolder"
    __type__ = "crypter"
    __version__ = "0.36"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?hotfile\.com/list/\w+/\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Hotfile.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.org")]
