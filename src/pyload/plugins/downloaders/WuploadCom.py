# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class WuploadCom(DeadDownloader):
    __name__ = "WuploadCom"
    __type__ = "downloader"
    __version__ = "0.28"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?wupload\..+?/file/((\w+/)?\d+)(/.*)?"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Wupload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"), ("Paul King", None)]
