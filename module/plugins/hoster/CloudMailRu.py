# -*- coding: utf-8 -*-

import base64
import urllib

from ..internal.Hoster import Hoster
from ..internal.misc import json


class CloudMailRu(Hoster):
    __name__ = "CloudMailRu"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'https?://cloud\.mail\.ru/dl\?q=(?P<QS>.+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool","Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cloud.mail.ru hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = r'"error":\s*"not_exists"'

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multiDL = True

    def process(self, pyfile):
        json_data = json.loads(base64.b64decode(self.info['pattern']['QS']))

        pyfile.name = urllib.unquote_plus(json_data['n']).encode('latin1').decode('utf8')
        pyfile.size = json_data['s']

        self.download(json_data['u'], disposition=False)
