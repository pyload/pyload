# -*- coding: utf-8 -*-

import time

import Crypto.Hash.SHA
import pycurl

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


def args(**kwargs):
    return kwargs


class DebridlinkFr(MultiHoster):
    __name__ = "DebridlinkFr"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback",
                   "bool",
                   "Fallback to free download if premium fails",
                   False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int",
                   "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Debrid-slink.fr multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://debrid-link.fr/api"

    def api_request(self, method, data=None, get={}, post={}):

        session = self.account.info['data'].get('session', None)
        if session:
            ts = str(int(time.time() - float(session['tsd'])))

            sha1 = Crypto.Hash.SHA.new()
            sha1.update(ts + method + session['key'])
            sign = sha1.hexdigest()

            self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-DL-TOKEN: " + session['token'],
                                                       "X-DL-SIGN: " + sign,
                                                       "X-DL-TS: " + ts])

        json_data = self.load(self.API_URL + method, get=get, post=post)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        res = self.api_request("/downloader/add", post=args(link=pyfile.url))

        if res['result'] == "OK":
            self.link = res['value']['downloadLink']
            pyfile.name = res['value'].get('filename', None) or pyfile.name
            self.resume_download = res['value'].get(
                'resume') or self.resume_download
            self.chunk_limit = res['value'].get('chunk') or self.chunk_limit
