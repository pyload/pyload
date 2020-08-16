# -*- coding: utf-8 -*-

#
# Test links:
# http://novafile.com/vfun4z6o2cit
# http://novafile.com/s6zrr5wemuz4

from ..base.xfs_downloader import XFSDownloader


class NovafileCom(XFSDownloader):
    __name__ = "NovafileCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?novafile\.com/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Novafile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
    ]

    PLUGIN_DOMAIN = "novafile.com"

    ERROR_PATTERN = r'class="alert.+?alert-separate".*?>\s*(?:<p>)?(.*?)\s*</'
    WAIT_PATTERN = r'<p>Please wait <span id="count".*?>(\d+)</span> seconds</p>'

    LINK_PATTERN = r'<a href="(http://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'
