# -*- coding: utf-8 -*-

import hashlib

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class UpfileVn(SimpleHoster):
    __name__ = "UpfileVn"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?upfile\.vn/(?P<ID>.+?)/.+?\.html'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Upfile.Vn hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'<h1>(?P<N>.+?) \((?P<S>[\d.,]+)(?P<U>[\w^_]+)\)</h1>'

    WAIT_PATTERN = r'data-count=\'(\d+)\''

    def handle_free(self, pyfile):
        token = hashlib.sha256(self.info['pattern']['ID'] + "7891").hexdigest().upper()

        self.data = self.load(pyfile.url,
                              post={'Token': token})

        json_data = json.loads(self.data)

        if json_data['Status'] is True:
            self.link = json_data['Link']

        else:
            self.log_debug("Download failed: %s" % json_data)
