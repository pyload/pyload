# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class FilerioCom(XFSPAccount):
    __name__    = "FilerioCom"
    __type__    = "account"
    __version__ = "0.02"

    __description__ = """FileRio.in account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_NAME = "filerio.in"
