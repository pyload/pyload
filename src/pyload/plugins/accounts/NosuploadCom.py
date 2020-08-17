# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class NosuploadCom(XFSAccount):
    __name__ = "NosuploadCom"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Nosupload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "nosupload.com"
