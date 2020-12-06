# -*- coding: utf-8 -*-
import json
import re

from ..base.multi_downloader import MultiDownloader


class PremiumizeMe(MultiDownloader):
    __name__ = "PremiumizeMe"
    __type__ = "downloader"
    __version__ = "0.34"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?premiumize\.me/file\?id=(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Premiumize.me multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Florian Franzen", "FlorianFranzen@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    DIRECT_LINK = False

    # See https://www.premiumize.me/api
    API_URL = "https://www.premiumize.me/api/"

    def api_respond(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        m = re.search(self.__pattern__, pyfile.url)
        if m is None:
            res = self.api_respond(
                "transfer/directdl",
                src=pyfile.url,
                apikey=self.account.info['login']['password']
            )

            if res['status'] == "success":
                self.pyfile.name = res['content'][0]['path']
                self.pyfile.size = res['content'][0]['size']
                self.download(res['content'][0]['link'])

            else:
                self.fail(res['message'])

        else:
            res = self.api_respond(
                "item/details",
                id=m.group('ID'),
                apikey=self.account.info['login']['password']
            )

            if res.get('status') != "error":
                self.pyfile.name = res['name']
                self.pyfile.size = res['size']
                self.download(res['link'])

            else:
                self.fail(res['message'])
