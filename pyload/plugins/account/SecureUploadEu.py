# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class SecureUploadEu(XFSPAccount):
    __name__ = "SecureUploadEu"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """SecureUpload.eu account plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.secureupload.eu/"
