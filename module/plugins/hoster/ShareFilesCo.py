# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class ShareFilesCo(DeadHoster):
    __name__ = "ShareFilesCo"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?sharefiles\.co/\w{12}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Sharefiles.co hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
