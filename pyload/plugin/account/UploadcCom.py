# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class UploadcCom(XFSAccount):
    __name    = "UploadcCom"
    __type    = "account"
    __version = "0.02"

    __description = """Uploadc.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "uploadc.com"
