# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class FilerioCom(XFSAccount):
    __name__    = "FilerioCom"
    __type__    = "account"
    __version__ = "0.03"

    __description__ = """FileRio.in account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "filerio.in"
