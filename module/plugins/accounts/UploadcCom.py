# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class UploadcCom(XFSPAccount):
    __name__ = "UploadcCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Uploadc.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.uploadc.com/"
