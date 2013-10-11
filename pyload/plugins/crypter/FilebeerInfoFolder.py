# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class FilebeerInfoFolder(DeadCrypter):
    __name__ = "FilebeerInfoFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?filebeer\.info/(\d+~f).*"
    __version__ = "0.02"
    __description__ = """Filebeer.info Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

