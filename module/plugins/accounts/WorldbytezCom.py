# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class WorldbytezCom(XFSAccount):
    __name__    = "WorldbytezCom"
    __type__    = "account"
    __version__ = "0.02"
    __status__  = "testing"

    __description__ = """Worldbytez.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "worldbytez.com"
