# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from pyload.plugin.account import Account


class Ftp(Account):
    __name__ = "Ftp"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Ftp dummy account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    login_timeout = info_threshold = 1000000
