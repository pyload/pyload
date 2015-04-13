# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class WuploadCom(DeadCrypter):
    __name    = "WuploadCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?wupload\.com/folder/\w+'
    __config  = []

    __description = """Wupload.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
