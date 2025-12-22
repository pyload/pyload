# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class KatfileCom(XFSAccount):
    __name__ = "KatfileCom"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """Katfile.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "katfile.cloud"
    PLUGIN_URL = "https://katfile.cloud"

    PREMIUM_PATTERN = r"Extend Premium account"
    VALID_UNTIL_PATTERN = r"<TD>Premium Pro account expire</TD><TD><b>(.+?)<"
    TRAFFIC_LEFT_PATTERN = r"Traffic available today.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?"
