# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class WuploadComFolder(DeadCrypter):
    __name__    = "WuploadComFolder"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?wupload\.com/folder/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Wupload.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(WuploadComFolder)
