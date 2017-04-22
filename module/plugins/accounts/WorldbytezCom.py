# -*- coding: utf-8 -*-

from ..internal.XFSAccount import XFSAccount


class WorldbytezCom(XFSAccount):
    __name__ = "WorldbytezCom"
    __type__ = "account"
    __version__ = "0.06"
    __status__ = "testing"

    __description__ = """Worldbytez.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "worldbytez.com"
