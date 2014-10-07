# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class NosuploadCom(XFSPAccount):
    __name__ = "NosuploadCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Nosupload.com account plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"


    HOSTER_URL = "http://www.nosupload.com/"
