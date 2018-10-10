# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class SpeedLoadOrg(DeadHoster):
    __name__ = "SpeedLoadOrg"
    __type__ = "hoster"
    __version__ = "1.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Speedload.org hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
