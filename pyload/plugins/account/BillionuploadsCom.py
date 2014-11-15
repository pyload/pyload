# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class BillionuploadsCom(XFSAccount):
    __name__    = "BillionuploadsCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """Billionuploads.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "billionuploads.com"
