# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class SpeedLoadOrg(DeadHoster):
    __name    = "SpeedLoadOrg"
    __type    = "hoster"
    __version = "1.02"

    __pattern = r'http://(?:www\.)?speedload\.org/(?P<ID>\w+)'
    __config  = []

    __description = """Speedload.org hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
