# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class MegauploadCom(DeadDownloader):
    __name__ = "MegauploadCom"
    __type__ = "downloader"
    __version__ = "0.36"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?megaupload\.com/\?.*&?(d|v)=\w+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Megaupload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net")]
