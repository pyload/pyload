# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class RapidfileshareNet(XFSDownloader):
    __name__ = "RapidfileshareNet"
    __type__ = "downloader"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?rapidfileshare\.net/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Rapidfileshare.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]

    PLUGIN_DOMAIN = "rapidfileshare.net"

    NAME_PATTERN = r'<input type="hidden" name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r">http://www.rapidfileshare.net/\w+?</font> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</font>"

    OFFLINE_PATTERN = r">No such file with this filename"
    TEMP_OFFLINE_PATTERN = (
        r"The page may have been renamed, removed or be temporarily unavailable.<"
    )
