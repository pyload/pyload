# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class HotfileCom(DeadCrypter):
    __name__    = "HotfileCom"
    __type__    = "crypter"
    __version__ = "0.30"

    __pattern__ = r'https?://(?:www\.)?hotfile\.com/list/\w+/\w+'
    __config__  = []

    __description__ = """Hotfile.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


getInfo = create_getInfo(HotfileCom)
