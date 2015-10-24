# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.plugins.internal.utils import json


class LinksnappyCom(MultiHoster):
    __name__    = "LinksnappyCom"
    __type__    = "hoster"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'https?://(?:[^/]+\.)?linksnappy\.com'
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Linksnappy.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def handle_premium(self, pyfile):
        host        = self._get_host(pyfile.url)
        json_params = json.dumps({'link'    : pyfile.url,
                                  'type'    : host,
                                  'username': self.account.user,
                                  'password': self.account.get_login('password')})

        r = self.load("http://linksnappy.com/api/linkgen",
                      post={'genLinks': json_params})

        self.log_debug("JSON data: " + r)

        j = json.loads(r)['links'][0]

        if j['error']:
            self.error(_("Error converting the link"))

        pyfile.name = j['filename']
        self.link   = j['generated']


    @staticmethod
    def _get_host(url):
        host = urlparse.urlsplit(url).netloc
        return re.search(r'[\w\-]+\.\w+$', host).group(0)


getInfo = create_getInfo(LinksnappyCom)
