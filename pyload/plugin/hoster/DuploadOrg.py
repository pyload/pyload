# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class DuploadOrg(DeadHoster):
    __name__    = "DuploadOrg"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?dupload\.org/\w{12}'
    __config__  = []

    __description__ = """Dupload.grg hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]
