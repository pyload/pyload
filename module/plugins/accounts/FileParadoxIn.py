# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class FileParadoxIn(XFSPAccount):
    __name__ = "FileParadoxIn"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """FileParadox.in account plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"


    HOSTER_URL = "http://www.fileparadox.in/"
