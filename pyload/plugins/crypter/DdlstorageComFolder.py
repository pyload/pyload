# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class DdlstorageComFolder(DeadCrypter):
    __name__ = "DdlstorageComFolder"
    __type__ = "crypter"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?ddlstorage\.com/folder/\w+'

    __description__ = """DDLStorage.com folder decrypter plugin"""
    __author_name__ = ("godofdream", "stickell")
    __author_mail__ = ("soilfiction@gmail.com", "l.stickell@yahoo.it")


getInfo = create_getInfo(SpeedLoadOrg)
