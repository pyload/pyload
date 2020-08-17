# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class SafesharingEu(XFSDownloader):
    __name__ = "SafesharingEu"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?safesharing\.eu/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Safesharing.eu downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    PLUGIN_DOMAIN = "safesharing.eu"

    ERROR_PATTERN = r'(?:<div class="alert alert-danger">)(.+?)(?:</div>)'
