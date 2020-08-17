# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class FileApeCom(DeadDownloader):
    __name__ = "FileApeCom"
    __type__ = "downloader"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = (
        r"http://(?:www\.)?fileape\.com/(index\.php\?act=download\&id=|dl/)\w+"
    )
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """FileApe.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("espes", None)]
