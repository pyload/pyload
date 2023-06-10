# -*- coding: utf-8 -*-

from ..internal.XFSAccount import XFSAccount


class FiregetCom(XFSAccount):
    __name__ = "FiregetCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """fireget.com account plugin"""
    __license__ = "GPLv3"

    PLUGIN_DOMAIN = "fireget.com"
    PLUGIN_URL = "https://fireget.com/"
