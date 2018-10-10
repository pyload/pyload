# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class HellspyCz(DeadHoster):
    __name__ = "HellspyCz"
    __type__ = "hoster"
    __version__ = "0.33"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?(?:hellspy\.(?:cz|com|sk|hu|pl)|sciagaj\.pl)(/\S+/\d+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """HellSpy.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
