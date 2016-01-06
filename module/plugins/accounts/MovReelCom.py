# -*- coding: utf-8 -*-

from module.plugins.internal.XFSAccount import XFSAccount


class MovReelCom(XFSAccount):
    __name__    = "MovReelCom"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Movreel.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


    login_timeout = 60
    info_threshold = 30

    PLUGIN_DOMAIN = "movreel.com"
