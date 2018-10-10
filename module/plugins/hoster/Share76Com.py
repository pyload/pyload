# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class Share76Com(DeadHoster):
    __name__ = "Share76Com"
    __type__ = "hoster"
    __version__ = "0.09"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?share76\.com/\w{12}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Share76.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = []
