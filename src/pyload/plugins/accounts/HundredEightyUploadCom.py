# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class HundredEightyUploadCom(XFSAccount):
    __name__ = "HundredEightyUploadCom"
    __type__ = "account"
    __version__ = "0.08"
    __status__ = "testing"

    __description__ = """180upload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "180upload.com"
