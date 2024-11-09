# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class WebshareCzFolder(BaseDecrypter):
    __name__ = "WebshareCzFolder"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:en\.)?webshare\.cz/(?:#/)?(?:folder/)(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
    ]

    __description__ = """Webshare.cz decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"</status><name>(.+?)</name>"
    LINK_PATTERN = r"<ident>(\w+?)</ident>"

    API_URL = "https://webshare.cz/api/"

    def api_request(self, method, **kwargs):
        return self.load(self.API_URL + method + "/", post=kwargs)

    def decrypt(self, pyfile):
        wst = self.account.get_data("wst") if self.account else ""
        api_data = self.api_request("folder", ident=self.info["pattern"]["ID"], offset=0, wst=wst)

        m = re.search(self.NAME_PATTERN, api_data)
        if m is not None:
            name = m.group(1)
        else:
            name = pyfile.package().name

        urls = ["https://webshare.cz/#/file/{}".format(link_id) for link_id in re.findall(self.LINK_PATTERN, api_data)]
        self.packages = [(name, urls, name)]
