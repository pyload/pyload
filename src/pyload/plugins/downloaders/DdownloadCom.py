# -*- coding: utf-8 -*-

import json
import pycurl
from ..base.xfs_downloader import XFSDownloader


class DdownloadCom(XFSDownloader):
    __name__ = "DdownloadCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:ddl\.to|ddownload\.com)/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Ddownload.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://ddownload.com/\g<ID>")]

    NAME_PATTERN = r'<div class="name position-relative">\s*<h4>(?P<N>.+?)</h4>'
    SIZE_PATTERN = r'<span class="file-size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>'

    OFFLINE_PATTERN = r"<h4>File Not Found</h4>"
    DL_LIMIT_PATTERN = r"You have to wait (.+?) till next download"

    API_KEY = "37699zuaj90n9hxado2m7"
    API_URL = "https://api-v2.ddownload.com/api/"

    #: See https://ddownload.com/api
    def api_request(self, method, **kwargs):
        kwargs.update({"key": self.API_KEY})
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def set_useragent(self):
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))

    def setup(self):
        super(DdownloadCom, self).setup()
        self.set_useragent()

    def load_account(self):
        self.set_useragent()
        super(DdownloadCom, self).load_account()

    # def api_info(self, url):
    #     info = {}
    #     api_data = self.api_request("file/info", file_code=re.match(self.__pattern__, url).group('ID'))
    #
    #     if api_data['status'] == 200:
    #         if api_data['result'][0]['status'] == 200:
    #             info['status'] = 2
    #             info['name'] = api_data['result'][0]['name']
    #             info['size'] = api_data['result'][0]['size']
    #
    #         else:
    #             info['status'] = 8
    #
    #     return info
