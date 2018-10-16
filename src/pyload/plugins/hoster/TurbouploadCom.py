# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class TurbouploadCom(DeadHoster):
    __name__ = "TurbouploadCom"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?turboupload\.com/(\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Turboupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
