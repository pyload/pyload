# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class FilebeerInfo(DeadHoster):
    __name__ = "FilebeerInfo"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?filebeer\.info/(?!\d*~f)(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Filebeer.info plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
