# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster


class X7To(DeadHoster):
    __name__ = "X7To"
    __type__ = "hoster"
    __version__ = "0.46"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?x7\.to/'
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """X7.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ernieb", "ernieb")]
