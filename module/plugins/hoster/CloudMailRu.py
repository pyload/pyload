# -*- coding: utf-8 -*-

import re

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class CloudMailRu(SimpleHoster):
    __name__ = "CloudMailRu"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://cloud\.mail\.ru/public/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool","Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Cloud.mail.ru hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'"name":\s*"(?P<N>.+?)",\s*"size":\s*(?P<S>\d+?),\s*"hash":'

    OFFLINE_PATTERN = r'"error":\s*"not_exists"'

    def handle_free(self, pyfile):
        m = re.search(r'window\["__configObject__\w+?"\]\s*=\s*({.+});', self.data, re.M)
        if m is None:
            self.fail(_("Json pattern not found"))

        json_data = json.loads(m.group(1).replace("\\x3c", "<"))

        self.link = "%s/%s?key=%s" % (json_data['dispatcher']['weblink_get'][0]['url'],
                                      json_data['request']['weblink'],
                                      json_data['params']['tokens']['download'])
