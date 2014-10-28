# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class FileParadoxIn(XFSPAccount):
    __name__    = "FileParadoxIn"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """FileParadox.in account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_NAME = "fileparadox.in"
