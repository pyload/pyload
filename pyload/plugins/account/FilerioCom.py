# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class FilerioCom(XFSAccount):
    __name    = "FilerioCom"
    __type    = "account"
    __version = "0.03"

    __description = """FileRio.in account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "filerio.in"
