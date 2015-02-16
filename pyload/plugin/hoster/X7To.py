# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class X7To(DeadHoster):
    __name    = "X7To"
    __type    = "hoster"
    __version = "0.41"

    __pattern = r'http://(?:www\.)?x7\.to/'

    __description = """X7.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("ernieb", "ernieb")]
