# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class FileomCom(XFSPAccount):
    __name__ = "FileomCom"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Fileom.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "fileom.com"
