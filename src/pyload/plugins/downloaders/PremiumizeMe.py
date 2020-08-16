# -*- coding: utf-8 -*-
import json
import urllib.parse

from ..base.multi_downloader import MultiDownloader


class PremiumizeMe(MultiDownloader):
    __name__ = "PremiumizeMe"
    __type__ = "downloader"
    __version__ = "0.31"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
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

    # See https://www.premiumize.me/static/api/api.html
    API_URL = "https://api.premiumize.me/pm-api/v1.php"

    def api_respond(self, method, user, password, **kwargs):
        get_params = {"method": method, "params[login]": user, "params[pass]": password}
        for key, val in kwargs.items():
            get_params["params[{}]".format(key)] = val

        json_data = self.load(self.API_URL, get=get_params)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        res = self.api_respond(
            "directdownloadlink",
            self.account.user,
            self.account.info["login"]["password"],
            link=pyfile.url,
        )

        status = res["status"]
        if status == 200:
            self.pyfile.name = res["result"]["filename"]
            self.pyfile.size = res["result"]["filesize"]

            # NOTE: Hack to avoid `fixurl()` "fixing" the URL query arguments :(
            urlp = urllib.parse.urlparse(res["result"]["location"])
            urlq = urllib.parse.parse_qsl(urlp.query)
            self.download(
                "{}://{}{}".format(urlp.scheme, urlp.netloc, urlp.path), get=urlq
            )

            # self.link        = res['result']['location']

        elif status == 400:
            self.fail(self._("Invalid url"))

        elif status == 404:
            self.offline()

        elif status >= 500:
            self.temp_offline()

        else:
            self.fail(res["statusmessage"])
