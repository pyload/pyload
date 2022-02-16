# -*- coding: utf-8 -*-

import base64
import json
import re

from ..base.downloader import BaseDownloader


class CloudMailRu(BaseDownloader):
    __name__ = "CloudMailRu"
    __type__ = "downloader"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"https?://cloud\.mail\.ru/dl\?q=(?P<QS>.+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Cloud.mail.ru downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = r'"error":\s*"not_exists"'

    def get_info(self, url="", html=""):
        info = super().get_info(url, html)

        qs = re.match(self.__pattern__, url).group('QS')
        file_info = json.loads(base64.b64decode(qs).decode("utf-8"))

        info.update({
            'name': file_info['n'],
            'size': file_info['s'],
            'u': file_info['u']
        })

        return info

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multi_dl = True

    def process(self, pyfile):
        self.download(self.info["u"], disposition=False)
