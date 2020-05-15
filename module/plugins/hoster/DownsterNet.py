# -*- coding: utf-8 -*-

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


class DownsterNet(MultiHoster):
    __name__ = "DownsterNet"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", False)]

    __description__ = """Downster.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    FILE_ERRORS = [("Error", r'{"state":"error"}'),
                   ("Retry", r'{"state":"retry"}')]

    API_URL = "https://downster.net/api/"

    def api_response(self, method, get={}, **kwargs):
        try:
            res = self.load(self.API_URL + method,
                            get=get,
                            post=json.dumps(kwargs))
        except BadHeader, e:
            res = e.content

        res = json.loads(res)

        return res

    def handle_free(self, pyfile):
        api_data = self.api_response("download/get",
                                     get={'url': pyfile.url})

        if not api_data['success']:
            if 'offline' in api_data['error']:
                self.offline()

            else:
                self.fail(api_data['error'])

        pyfile.name = api_data['data']['name']
        pyfile.size = int(api_data['data']['size'])

        self.link = api_data['data']['downloadUrl']
