# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DdlstorageComFolder(SimpleCrypter):
    __name__ = "DdlstorageComFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?ddlstorage.com/folder/\w{10}'

    __description__ = """DDLStorage.com folder decrypter plugin"""
    __author_name__ = ("godofdream", "stickell")
    __author_mail__ = ("soilfiction@gmail.com", "l.stickell@yahoo.it")

    LINK_PATTERN = r'<a class="sub_title" style="text-decoration:none;" href="(http://www.ddlstorage.com/.*)">'
