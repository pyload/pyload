# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class X7To(DeadHoster):
    __name__    = "X7To"
    __type__    = "hoster"
    __version__ = "0.42"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?x7\.to/'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """X7.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("ernieb", "ernieb")]


getInfo = create_getInfo(X7To)
