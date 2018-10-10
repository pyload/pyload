# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class FileApeCom(DeadHoster):
    __name__ = "FileApeCom"
    __type__ = "hoster"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """FileApe.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("espes", None)]
