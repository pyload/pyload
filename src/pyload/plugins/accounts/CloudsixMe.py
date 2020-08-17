# -*- coding: utf-8 -*-

from ..base.xfs_account import XFSAccount


class CloudsixMe(XFSAccount):
    __name__ = "CloudsixMe"
    __type__ = "account"
    __version__ = "0.05"
    __status__ = "testing"

    __description__ = """Cloudsix.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "cloudsix.me"
