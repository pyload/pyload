# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSPAccount import XFSPAccount


class FilerioCom(XFSPAccount):
    __name__ = "FilerioCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """FileRio.in account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_URL = "http://www.filerio.in/"
