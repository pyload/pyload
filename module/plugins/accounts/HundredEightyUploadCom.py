# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class HundredEightyUploadCom(XFSPAccount):
    __name__    = "HundredEightyUploadCom"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """180upload.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "180upload.com"
