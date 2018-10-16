# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class FreevideoCz(DeadHoster):
    __name__ = "FreevideoCz"
    __type__ = "hoster"
    __version__ = "0.35"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?freevideo\.cz/vase-videa/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Freevideo.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
