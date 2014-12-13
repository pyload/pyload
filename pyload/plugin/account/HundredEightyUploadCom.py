# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class HundredEightyUploadCom(XFSAccount):
    __name    = "HundredEightyUploadCom"
    __type    = "account"
    __version = "0.02"

    __description = """180upload.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "180upload.com"
