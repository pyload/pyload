# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class JunkyvideoCom(XFSAccount):
    __name__    = "JunkyvideoCom"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """Junkyvideo.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "junkyvideo.com"
