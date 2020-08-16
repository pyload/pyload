# -*- coding: utf-8 -*-

from ..base.xfs_downloader import XFSDownloader


class SecureUploadEu(XFSDownloader):
    __name__ = "SecureUploadEu"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?secureupload\.eu/\w{12}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """SecureUpload.eu downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]

    PLUGIN_DOMAIN = "secureupload.eu"

    INFO_PATTERN = r"<h3>Downloading (?P<N>.+?) \((?P<S>.+?)\)</h3>"
