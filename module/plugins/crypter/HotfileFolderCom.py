# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class HotfileFolderCom(DeadCrypter):
    __name__ = "HotfileFolderCom"
    __type__ = "crypter"
    __version__ = "0.2"

    __pattern__ = r'https)://(?:www\.)?hotfile\.com/list/\w+/\w+'

    __description__ = """Hotfile.com folder decrypter plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"
