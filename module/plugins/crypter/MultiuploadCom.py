# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class MultiuploadCom(DeadCrypter):
    __name__    = "MultiuploadCom"
    __type__    = "crypter"
    __version__ = "0.06"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?multiupload\.(com|nl)/\w+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """MultiUpload.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
