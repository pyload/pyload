# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class VidPlayNet(XFSAccount):
    __name    = "VidPlayNet"
    __type    = "account"
    __version = "0.02"

    __description = """VidPlay.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "vidplay.net"
