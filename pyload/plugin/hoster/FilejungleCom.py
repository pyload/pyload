# -*- coding: utf-8 -*-

from pyload.plugin.hoster.FileserveCom import FileserveCom, checkFile
from pyload.plugin.Plugin import chunks


class FilejungleCom(FileserveCom):
    __name    = "FilejungleCom"
    __type    = "hoster"
    __version = "0.51"

    __pattern = r'http://(?:www\.)?filejungle\.com/f/(?P<id>[^/]+).*'

    __description = """Filejungle.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    URLS = ["http://www.filejungle.com/f/", "http://www.filejungle.com/check_links.php",
            "http://www.filejungle.com/checkReCaptcha.php"]
    LINKCHECK_TR = r'<li>\s*(<div class="col1">.*?)</li>'
    LINKCHECK_TD = r'<div class="(?:col )?col\d">(?:<[^>]*>|&nbsp;)*([^<]*)'

    LONG_WAIT_PATTERN = r'<h1>Please wait for (\d+) (\w+)\s*to download the next file\.</h1>'


def getInfo(urls):
    for chunk in chunks(urls, 100):
        yield checkFile(FilejungleCom, chunk)
