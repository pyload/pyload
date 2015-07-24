# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UnrestrictLi(DeadHoster):
    __name__    = "UnrestrictLi"
    __type__    = "hoster"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(unrestrict|unr)\.li/dl/[\w^_]+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Unrestrict.li multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(UnrestrictLi)
