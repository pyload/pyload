# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class RarefileNet(XFSAccount):
    __name__    = "RarefileNet"
    __type__    = "account"
    __version__ = "0.08"
    __status__  = "testing"

    __description__ = """RareFile.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    PLUGIN_DOMAIN = "rarefile.net"
