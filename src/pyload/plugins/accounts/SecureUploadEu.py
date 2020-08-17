# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class SecureUploadEu(XFSAccount):
    __name__ = "SecureUploadEu"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """SecureUpload.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "secureupload.eu"
