# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class NowDownloadSx(DeadDownloader):
    __name__ = "NowDownloadSx"
    __type__ = "downloader"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?(nowdownload\.[a-zA-Z]{2,}/(dl/|download\.php.+?id=|mobile/(#/files/|.+?id=))|likeupload\.org/)\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """NowDownload.sx downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("godofdream", "soilfiction@gmail.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]
