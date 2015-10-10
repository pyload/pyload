# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SpeedLoadOrg(DeadHoster):
    __name__    = "SpeedLoadOrg"
    __type__    = "hoster"
    __version__ = "1.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?speedload\.org/(?P<ID>\w+)'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Speedload.org hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(SpeedLoadOrg)
