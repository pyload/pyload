# -*- coding: utf-8 -*-

from ..internal.SimpleHoster import SimpleHoster
from ..internal.misc import json

class IronfilesNet(SimpleHoster):
    __name__ = "IronfilesNet"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://ironfiles\.net/file/download/id/(?P<ID>\d+)(?:/key/(?P<KEY>65a2bfa38c2c1899))?'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Ironfiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LOGIN_PREMIUM = True

    OFFLINE_PATTERN = "^unmatchable$"

    API_URL = "https://ironfiles.net/api/"

    def api_response(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def handle_premium(self, pyfile):
        _id = self.info['pattern']['ID']
        _key = self.info['pattern']['KEY']

        file_info = json.loads(self.load("https://ironfiles.net/api/fileInfo/file/" + _id +
                                         ("/key/" + _key) if _key else ""))

        if file_info['result']:
            pyfile.name = file_info['filename']
            pyfile.size = file_info['size']
            self.link = "https://ironfiles.net/download/file/id/" + _id + ("/key/" + _key) if _key else ""

        else:
            message = file_info['message']
            if message == "File not available":
                self.offline()

            else:
                self.fail(message)

