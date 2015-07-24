# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class NosuploadCom(XFSAccount):
    __name__    = "NosuploadCom"
    __type__    = "account"
    __version__ = "0.03"
    __status__  = "testing"

    __description__ = """Nosupload.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "nosupload.com"
