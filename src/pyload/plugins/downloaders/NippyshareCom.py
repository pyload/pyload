# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class NippyshareCom(XFSDownloader):
    __name__ = "NippyshareCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://nippyshare.com/v/\w{6}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Nippyshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("OzzieIsaacs", "Ozzie.Fernandez.Isaacs@googlemail.com")]

    PLUGIN_DOMAIN = "nippyshare.com"

    NAME_PATTERN = r"><li>Name:(?P<N>.+?)</li>"
    SIZE_PATTERN = r"<li>Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)</li>"

    LINK_PATTERN = r"<a href='(.+?)' class='btn btn-info center-block'>Download</a>"
