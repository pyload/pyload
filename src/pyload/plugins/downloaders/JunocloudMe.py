# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class JunocloudMe(XFSDownloader):
    __name__ = "JunocloudMe"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:\w+\.)?junocloud\.me/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Junocloud.me downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]

    PLUGIN_DOMAIN = "junocloud.me"

    URL_REPLACEMENTS = [(r"//(www\.)?junocloud", "//dl3.junocloud")]

    OFFLINE_PATTERN = r">No such file with this filename<"
    TEMP_OFFLINE_PATTERN = (
        r"The page may have been renamed, removed or be temporarily unavailable.<"
    )
