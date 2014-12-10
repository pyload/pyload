# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSAccount import XFSAccount


class MovReelCom(XFSAccount):
    __name    = "MovReelCom"
    __type    = "account"
    __version = "0.03"

    __description = """Movreel.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


    login_timeout = 60
    info_threshold = 30

    HOSTER_DOMAIN = "movreel.com"
