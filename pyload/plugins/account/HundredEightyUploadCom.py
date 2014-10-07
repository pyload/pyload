# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class HundredEightyUploadCom(XFSPAccount):
    __name__ = "HundredEightyUploadCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """180upload.com account plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.180upload.com/"
