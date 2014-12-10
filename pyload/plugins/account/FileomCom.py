# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class FileomCom(XFSAccount):
    __name    = "FileomCom"
    __type    = "account"
    __version = "0.02"

    __description = """Fileom.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "fileom.com"
