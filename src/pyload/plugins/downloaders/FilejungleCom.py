# -*- coding: utf-8 -*-

from .FileserveCom import FileserveCom


class FilejungleCom(FileserveCom):
    __name__ = "FilejungleCom"
    __type__ = "downloader"
    __version__ = "0.57"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?filejungle\.com/f/(?P<ID>[^/]+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Filejungle.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    URLS = [
        "http://www.filejungle.com/f/",
        "http://www.filejungle.com/check_links.php",
        "http://www.filejungle.com/checkReCaptcha.php",
    ]
    LINKCHECK_TR = r'<li>\s*(<div class="col1">.*?)</li>'
    LINKCHECK_TD = r'<div class="(?:col )?col\d">(?:<.*?>|&nbsp;)*([^<]*)'

    LONG_WAIT_PATTERN = (
        r"<h1>Please wait for (\d+) (\w+)\s*to download the next file\.</h1>"
    )
