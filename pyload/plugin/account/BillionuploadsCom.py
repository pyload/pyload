# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class BillionuploadsCom(XFSAccount):
    __name    = "BillionuploadsCom"
    __type    = "account"
    __version = "0.02"

    __description = """Billionuploads.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "billionuploads.com"
