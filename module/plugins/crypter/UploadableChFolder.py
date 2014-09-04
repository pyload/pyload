# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadableChFolder(SimpleCrypter):
    __name__ = "UploadableChFolder"
    __type__ = "crypter"
    __pattern__ = r'http://(?:www\.)?uploadable\.ch/list/\w+'
    __version__ = "0.01"
    __description__ = """Uploadable.ch folder decrypter plugin"""
    __author_name__ = ("guidobelix")
    __author_mail__ = ("guidobelix@hotmail.it")

    LINK_PATTERN = r'<a href="(http://www.uploadable.ch/file/\w+)" class="icon_zipfile">'
