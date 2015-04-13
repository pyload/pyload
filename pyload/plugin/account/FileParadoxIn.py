# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class FileParadoxIn(XFSAccount):
    __name    = "FileParadoxIn"
    __type    = "account"
    __version = "0.02"

    __description = """FileParadox.in account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "fileparadox.in"
