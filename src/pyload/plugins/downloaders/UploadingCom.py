# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class UploadingCom(DeadDownloader):
    __name__ = "UploadingCom"
    __type__ = "downloader"
    __version__ = "0.51"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?uploading\.com/files/(?:get/)?(?P<ID>\w+)"

    __description__ = """Uploading.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("mkaay", "mkaay@mkaay.de"),
        ("zoidberg", "zoidberg@mujmail.cz"),
    ]
