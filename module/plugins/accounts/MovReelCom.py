# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class MovReelCom(XFSPAccount):
    __name__ = "MovReelCom"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Movreel.com account plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    login_timeout = 60
    info_threshold = 30

    HOSTER_URL = "http://movreel.com/"

    TRAFFIC_LEFT_PATTERN = r'Traffic.*?<b>([^<]+)</b>'
    LOGIN_FAIL_PATTERN = r'<b[^>]*>Incorrect Login or Password</b><br>'
