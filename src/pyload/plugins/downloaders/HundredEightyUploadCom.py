# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class HundredEightyUploadCom(XFSDownloader):
    __name__ = "HundredEightyUploadCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?180upload\.com/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """180upload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    PLUGIN_DOMAIN = "180upload.com"

    OFFLINE_PATTERN = r">File Not Found"
