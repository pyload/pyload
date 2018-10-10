# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class Vipleech4UCom(DeadHoster):
    __name__ = "Vipleech4UCom"
    __type__ = "hoster"
    __version__ = "0.25"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?vipleech4u\.com/manager\.php'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Vipleech4u.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Kagenoshin", "kagenoshin@gmx.ch")]
