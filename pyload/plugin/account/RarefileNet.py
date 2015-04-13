# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class RarefileNet(XFSAccount):
    __name    = "RarefileNet"
    __type    = "account"
    __version = "0.04"

    __description = """RareFile.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_DOMAIN = "rarefile.net"
