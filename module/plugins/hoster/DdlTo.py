# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url

from ..internal.misc import json
from ..internal.XFSHoster import XFSHoster


class DdlTo(XFSHoster):
    __name__ = "DdlTo"
    __type__ = "hoster"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:ddl\.to|ddownload\.com)/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Ddl.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "ddownload.com"

    URL_REPLACEMENTS = [(__pattern__ + '.*', r"https://ddownload.com/\g<ID>")]

    NAME_PATTERN = r'<div class="name">\s*<h4>(?P<N>.+?)</h4>'
    SIZE_PATTERN = r'<div class="name">.+?<span>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</span>', re.S

    OFFLINE_PATTERN = r'<h4>File Not Found</h4>'
    DL_LIMIT_PATTERN = r'You have to wait (.+?) till next download'

    API_KEY = "37699zuaj90n9hxado2m7"
    API_URL = "https://api-v2.ddl.to/api/"

    @classmethod
    def api_response(cls, method, **kwargs):
        kwargs.update({'key': cls.API_KEY})
        json_data = get_url(cls.API_URL + method, get=kwargs)
        return json.loads(json_data)

    @classmethod
    def api_info(cls, url):
        info = {}
        api_data = cls.api_response("file/info", file_code=re.match(cls.__pattern__, url).group('ID'))

        if api_data['status'] == 200:
            if api_data['result'][0]['status'] == 200:
                info['status'] = 2
                info['name'] = api_data['result'][0]['name']
                info['size'] = api_data['result'][0]['size']

            else:
                info['status'] = 8

        return info
