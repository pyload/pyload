# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class SharebeastCom(XFSAccount):
    __name__ = "SharebeastCom"
    __type__ = "account"
    __version__ = "0.06"
    __status__ = "testing"

    __description__ = """Sharebeast.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "sharebeast.com"
