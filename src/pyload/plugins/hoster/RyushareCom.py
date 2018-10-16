# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class RyushareCom(DeadHoster):
    __name__ = "RyushareCom"
    __type__ = "hoster"
    __version__ = "0.32"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?ryushare\.com/\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Ryushare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("quareevo", "quareevo@arcor.de"),
    ]
