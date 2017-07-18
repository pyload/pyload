# -*- coding: utf-8 -*-

import random
import re

from module.network.RequestFactory import getURL as get_url

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import json


class TenluaVn(SimpleHoster):
    __name__ = "TenluaVn"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?tenlua\.vn(?!/folder)(?:/.*)?/(?P<ID>[0-9a-f]{16})/'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Tenlua.vn hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://api2.tenlua.vn/"

    @classmethod
    def api_response(cls, method, **kwargs):
        kwargs['a'] = method
        return json.loads(get_url(cls.API_URL, post=json.dumps([kwargs])))

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group('ID')
        r = "0." + "".join([random.choice("0123456789") for x in range(16)])
        file_info = cls.api_response("filemanager_builddownload_getinfo", n=file_id, r=r)

        return {'name': file_info[0]['n'],
                'size': file_info[0]['real_size'],
                'dlink': file_info[0]['dlink']}

    def handle_free(self, pyfile):
        self.wait(30)
        self.link = self.info['dlink']
