# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class CyberlockerCh(DeadHoster):
    __name__ = "CyberlockerCh"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?cyberlocker\.ch/\w+'

    __description__ = """Cyberlocker.ch hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


getInfo = create_getInfo(CyberlockerCh)
