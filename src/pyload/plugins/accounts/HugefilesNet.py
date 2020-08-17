# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class HugefilesNet(XFSAccount):
    __name__ = "HugefilesNet"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Hugefiles.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "hugefiles.net"
