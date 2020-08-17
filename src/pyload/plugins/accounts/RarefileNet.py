# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class RarefileNet(XFSAccount):
    __name__ = "RarefileNet"
    __type__ = "account"
    __version__ = "0.09"
    __status__ = "testing"

    __description__ = """RareFile.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    PLUGIN_DOMAIN = "rarefile.net"
