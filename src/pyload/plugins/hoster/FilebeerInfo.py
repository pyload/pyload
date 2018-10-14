# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class FilebeerInfo(DeadHoster):
    __name__ = "FilebeerInfo"
    __type__ = "hoster"
    __version__ = "0.08"
    __pyload_version__ = "0.5"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Filebeer.info plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
