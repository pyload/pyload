# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class FreevideoCz(DeadHoster):
    __name    = "FreevideoCz"
    __type    = "hoster"
    __version = "0.30"

    __pattern = r'http://(?:www\.)?freevideo\.cz/vase-videa/.+'
    __config  = []

    __description = """Freevideo.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
