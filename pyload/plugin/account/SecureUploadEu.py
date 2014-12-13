# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class SecureUploadEu(XFSAccount):
    __name    = "SecureUploadEu"
    __type    = "account"
    __version = "0.02"

    __description = """SecureUpload.eu account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "secureupload.eu"
