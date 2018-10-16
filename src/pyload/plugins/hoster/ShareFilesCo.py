# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class ShareFilesCo(DeadHoster):
    __name__ = "ShareFilesCo"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?sharefiles\.co/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Sharefiles.co hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]
