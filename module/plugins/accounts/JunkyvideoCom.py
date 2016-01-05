# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class JunkyvideoCom(XFSAccount):
    __name__    = "JunkyvideoCom"
    __type__    = "account"
    __version__ = "0.05"
    __status__  = "testing"

    __description__ = """Junkyvideo.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = "junkyvideo.com"
