# -*- coding: utf-8 -*-

# ATTENTION: if you cannot see the interactive captcha (on firefox), make sure to activate/install X-Frame-Options Header:
# https://addons.mozilla.org/en-US/firefox/addon/ignore-x-frame-options-header/

import re

from ..base.xfs_downloader import XFSDownloader


class FileAl(XFSDownloader):
    __name__ = "FileAl"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?file\.al/\w{12}"

    __description__ = """File.al downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", None)]

    PLUGIN_DOMAIN = "file.al"
    LINK_PATTERN = (
        r'direct link.*?<a [^>]*href="(.+?)".*?>Click here to download',
        re.MULTILINE | re.DOTALL,
    )
    WAIT_PATTERN = r"countdown.*?seconds.*?(\d+)"

    RECAPTCHA_PATTERN = r"g-recaptcha.*?sitekey=[\"']([^\"]*)"
    PREMIUM_ONLY_PATTERN = r"(?:[Pp]remium Users only|can download files up to.*only)"

    def setup(self):
        self.multi_dl = self.premium
        self.resume_download = True
