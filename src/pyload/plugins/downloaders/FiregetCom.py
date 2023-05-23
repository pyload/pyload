# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class FiregetCom(XFSDownloader):
    __name__ = "FiregetCom"
    __type__ = "downloader"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?fireget\.com/(?P<ID>\w{12})/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Fireget.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r">You have requested .+?> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)"

    WAIT_PATTERN = r'<span id="countdown_str">.+?<span .+?>(\d+)</span>'
    DL_LIMIT_PATTERN = r">You have to wait (.+?) till next download<"

    OFFLINE_PATTERN = r"File Not Found|No such file with this filename"
    TEMP_OFFLINE_PATTERN = (
        r"Connection limit reached|Server error|You have reached the download limit"
    )

    PLUGIN_DOMAIN = "fireget.com"
