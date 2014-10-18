# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class SecureUploadEu(XFSPAccount):
    __name__ = "SecureUploadEu"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """SecureUpload.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "secureupload.eu"
