# -*- coding: utf-8 -*-

from ..base.account import BaseAccount


class Ftp(BaseAccount):
    __name__ = "Ftp"
    __type__ = "account"
    __version__ = "0.07"
    __status__ = "testing"

    __description__ = """Ftp dummy account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    info_threshold = 1_000_000
    login_timeout = 1_000_000
