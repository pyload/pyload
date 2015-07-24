# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class EgoFilesCom(DeadHoster):
    __name__    = "EgoFilesCom"
    __type__    = "hoster"
    __version__ = "0.17"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?egofiles\.com/\w+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Egofiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(EgoFilesCom)
