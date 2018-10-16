# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class EgoFilesCom(DeadHoster):
    __name__ = "EgoFilesCom"
    __type__ = "hoster"
    __version__ = "0.21"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"https?://(?:www\.)?egofiles\.com/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Egofiles.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
