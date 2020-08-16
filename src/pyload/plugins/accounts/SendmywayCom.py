# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class SendmywayCom(XFSAccount):
    __name__ = "SendmywayCom"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Sendmyway.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "sendmyway.com"
