# -*- coding: utf-8 -*-

from module.plugins.hoster.FileserveCom import FileserveCom, checkFile
from module.plugins.Plugin import chunks


class FilejungleCom(FileserveCom):
    __name__ = "FilejungleCom"
    __type__ = "hoster"
    __version__ = "0.51"

    __pattern__ = r'http://(?:www\.)?filejungle\.com/f/(?P<id>[^/]+).*'

    __description__ = """Filejungle.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    URLS = ["http://www.filejungle.com/f/", "http://www.filejungle.com/check_links.php",
            "http://www.filejungle.com/checkReCaptcha.php"]
    LINKCHECK_TR = r'<li>\s*(<div class="col1">.*?)</li>'
    LINKCHECK_TD = r'<div class="(?:col )?col\d">(?:<[^>]*>|&nbsp;)*([^<]*)'

    LONG_WAIT_PATTERN = r'<h1>Please wait for (\d+) (\w+)\s*to download the next file\.</h1>'


def getInfo(urls):
    for chunk in chunks(urls, 100):
        yield checkFile(FilejungleCom, chunk)
