# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class CyberlockerCh(DeadHoster):
    __name__ = "CyberlockerCh"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?cyberlocker\.ch/\w+'

    __description__ = """Cyberlocker.ch hoster plugin"""
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(CyberlockerCh)
