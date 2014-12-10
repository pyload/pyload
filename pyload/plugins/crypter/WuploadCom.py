# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class WuploadCom(DeadCrypter):
    __name    = "WuploadCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?wupload\.com/folder/\w+'

    __description = """Wupload.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(WuploadCom)
