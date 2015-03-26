# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class DuploadOrg(DeadHoster):
    __name    = "DuploadOrg"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?dupload\.org/\w{12}'
    __config  = []

    __description = """Dupload.grg hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
