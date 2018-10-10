# -*- coding: utf-8 -*-

from .ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name__ = "MultihostersCom"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)multihosters\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Multihosters.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("tjeh", "tjeh@gmx.net")]
