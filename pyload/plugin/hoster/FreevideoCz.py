# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class FreevideoCz(DeadHoster):
    __name__    = "FreevideoCz"
    __type__    = "hoster"
    __version__ = "0.30"

    __pattern__ = r'http://(?:www\.)?freevideo\.cz/vase-videa/.+'
    __config__  = []

    __description__ = """Freevideo.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
