# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class MegauploadComFolder(DeadCrypter):
    __name__    = "MegauploadComFolder"
    __type__    = "crypter"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?megaupload\.com/(\?f|xml/folderfiles\.php\?.*&?folderid)=\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Megaupload.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(MegauploadComFolder)
