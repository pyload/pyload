# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class X7To(DeadHoster):
    __name    = "X7To"
    __type    = "hoster"
    __version = "0.41"

    __pattern = r'http://(?:www\.)?x7\.to/'

    __description = """X7.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("ernieb", "ernieb")]


getInfo = create_getInfo(X7To)
