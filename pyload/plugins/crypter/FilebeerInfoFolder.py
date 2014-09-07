# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter


class FilebeerInfoFolder(DeadCrypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?filebeer\.info/(\d+~f).*'

    __description__ = """Filebeer.info folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"
