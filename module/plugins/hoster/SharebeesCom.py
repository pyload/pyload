# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class SharebeesCom(DeadHoster):
    __name__ = "SharebeesCom"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?sharebees\.com/\w{12}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """ShareBees hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
