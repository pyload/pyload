# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class NovafileCom(XFSAccount):
    __name__ = "NovafileCom"
    __type__ = "account"
    __version__ = "0.08"
    __status__ = "testing"

    __description__ = """Novafile.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")
    ]

    PLUGIN_DOMAIN = "novafile.org"
    LOGIN_URL = "https://novafile.org/login"

    TRAFFIC_LEFT_PATTERN = r"Traffic Available:.*?</td>\s*<td>(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</td>"
