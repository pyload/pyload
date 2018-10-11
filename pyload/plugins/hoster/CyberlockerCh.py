# -*- coding: utf-8 -*-
from builtins import _

from pyload.plugins.internal.DeadHoster import DeadHoster


class CyberlockerCh(DeadHoster):
    __name__ = "CyberlockerCh"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?cyberlocker\.ch/\w+'
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Cyberlocker.ch hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
