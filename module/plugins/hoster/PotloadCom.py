# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class PotloadCom(DeadHoster):
    __name__ = "PotloadCom"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?potload\.com/\w{12}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Potload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
