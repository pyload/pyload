# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class FilerioCom(XFSPAccount):
    __name__ = "FilerioCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """FileRio.in account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    HOSTER_URL = "http://filerio.in/"
