# -*- coding: utf-8 -*-

from ..internal.deadhoster import DeadHoster


class PandaplaNet(DeadHoster):
    __name__ = "PandaplaNet"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?pandapla\.net/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Pandapla.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
