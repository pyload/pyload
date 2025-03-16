# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class Mp4uploadCom(XFSAccount):
    __name__ = "Mp4uploadCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Mp4upload.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "mp4upload.com"
    LOGIN_URL = "https://www.mp4upload.com/login"
    LOGIN_SKIP_PATTERN = r"https://www\.mp4upload\.com/logout/"
    PREMIUM_PATTERN = r">Premium Account"
    VALID_UNTIL_PATTERN = r"Premium expiration:.*?>(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    VALID_UNTIL_FORMAT = "%Y-%m-%d %H:%M:%S"
