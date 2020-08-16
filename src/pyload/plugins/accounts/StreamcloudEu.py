# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class StreamcloudEu(XFSAccount):
    __name__ = "StreamcloudEu"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Streamcloud.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "streamcloud.eu"
