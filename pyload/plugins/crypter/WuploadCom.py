# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class WuploadCom(DeadCrypter):
    __name__    = "WuploadCom"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?wupload\.com/folder/\w+'

    __description__ = """Wupload.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(WuploadCom)
