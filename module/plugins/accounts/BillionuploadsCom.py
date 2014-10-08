# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class BillionuploadsCom(XFSPAccount):
    __name__ = "BillionuploadsCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Billionuploads.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.billionuploads.com/"
