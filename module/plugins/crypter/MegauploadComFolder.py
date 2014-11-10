# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class MegauploadComFolder(DeadCrypter):
    __name__    = "MegauploadComFolder"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?megaupload\.com/(\?f|xml/folderfiles\.php\?.*&?folderid)=\w+'

    __description__ = """Megaupload.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
