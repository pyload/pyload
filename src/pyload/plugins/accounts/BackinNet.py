# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class BackinNet(XFSAccount):
    __name__ = "BackinNet"
    __type__ = "account"
    __version__ = "0.06"
    __status__ = "testing"

    __description__ = """Backin.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "backin.net"
