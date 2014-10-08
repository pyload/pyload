# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class X7To(DeadHoster):
    __name__ = "X7To"
    __type__ = "hoster"
    __version__ = "0.41"

    __pattern__ = r'http://(?:www\.)?x7.to/'

    __description__ = """X7.to hoster plugin"""
    __authors__ = [("ernieb", "ernieb")]


getInfo = create_getInfo(X7To)
