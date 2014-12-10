# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class NosuploadCom(XFSAccount):
    __name    = "NosuploadCom"
    __type    = "account"
    __version = "0.02"

    __description = """Nosupload.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "nosupload.com"
