# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class KatfileCom(XFSDownloader):
    __name__ = "KatfileCom"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?katfile\.com/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """katfile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)"'
    SIZE_PATTERN = r'<span id="fsize" .+?>(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'

    WAIT_PATTERN = r"(?:var estimated_time = |Delay between free downloads must be not less than )([\w ]+?)[.;]"
    LINK_PATTERN = r'<a href="([^"]+)" id="dlink"'

    PLUGIN_DOMAIN = "katfile.com"
