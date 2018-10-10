# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class EgoFilesCom(DeadHoster):
    __name__ = "EgoFilesCom"
    __type__ = "hoster"
    __version__ = "0.21"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?egofiles\.com/\w+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Egofiles.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
