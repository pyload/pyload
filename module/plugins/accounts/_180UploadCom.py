# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class _180UploadCom(XFSAccount):
    __name__    = "180UploadCom"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """180upload.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "180upload.com"
