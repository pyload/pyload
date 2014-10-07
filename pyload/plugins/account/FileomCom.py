# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class FileomCom(XFSPAccount):
    __name__ = "FileomCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Fileom.com account plugin"""
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_URL = "http://www.fileom.com/"
