# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class FilejokerNet(XFSAccount):
    __name__ = "FilejokerNet"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __description__ = """Filejoker.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "filejoker.net"
