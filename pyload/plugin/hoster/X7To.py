# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class X7To(DeadHoster):
    __name__    = "X7To"
    __type__    = "hoster"
    __version__ = "0.41"

    __pattern__ = r'http://(?:www\.)?x7\.to/'

    __description__ = """X7.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("ernieb", "ernieb")]
