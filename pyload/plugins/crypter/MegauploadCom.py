# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class MegauploadCom(DeadCrypter):
    __name    = "MegauploadCom"
    __type    = "crypter"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?megaupload\.com/(\?f|xml/folderfiles\.php\?.*&?folderid)=\w+'

    __description = """Megaupload.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(MegauploadCom)
