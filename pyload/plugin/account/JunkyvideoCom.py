# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class JunkyvideoCom(XFSAccount):
    __name    = "JunkyvideoCom"
    __type    = "account"
    __version = "0.01"

    __description = """Junkyvideo.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "junkyvideo.com"
