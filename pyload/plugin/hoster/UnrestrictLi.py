# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UnrestrictLi(DeadHoster):
    __name    = "UnrestrictLi"
    __type    = "hoster"
    __version = "0.23"

    __pattern = r'https?://(?:www\.)?(unrestrict|unr)\.li/dl/[\w^_]+'

    __description = """Unrestrict.li multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]
