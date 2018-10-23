# -*- coding: utf-8 -*-

from ..internal.deadhoster import DeadHoster


class FilezyNet(DeadHoster):
    __name__ = "FilezyNet"
    __type__ = "hoster"
    __version__ = "0.25"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?filezy\.net/\w{12}"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Filezy.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = []
