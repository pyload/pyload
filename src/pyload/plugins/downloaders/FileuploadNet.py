# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class FileuploadNet(SimpleDownloader):
    __name__ = "FileuploadNet"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(en\.)?file-upload\.net/download-\d+/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """File-upload.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r"<title>File-Upload.net - (?P<N>.+?)<"
    SIZE_PATTERN = r"</label><span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = r"Datei existiert nicht"

    LINK_FREE_PATTERN = r"<a href='(.+?)' title='download' onclick"

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
