# -*- coding: utf-8 -*-

import re

from urlparse import urlsplit

from pyload.utils import json_loads, json_dumps
from pyload.plugin.internal.MultiHoster import MultiHoster


class LinksnappyCom(MultiHoster):
    __name    = "LinksnappyCom"
    __type    = "hoster"
    __version = "0.08"

    __pattern = r'https?://(?:[^/]+\.)?linksnappy\.com'

    __description = """Linksnappy.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    SINGLE_CHUNK_HOSTERS = ["easybytez.com"]


    def handlePremium(self, pyfile):
        host        = self._get_host(pyfile.url)
        json_params = json_dumps({'link'    : pyfile.url,
                                  'type'    : host,
                                  'username': self.user,
                                  'password': self.account.getAccountData(self.user)['password']})

        r = self.load("http://gen.linksnappy.com/genAPI.php",
                      post={'genLinks': json_params})

        self.logDebug("JSON data: " + r)

        j = json_loads(r)['links'][0]

        if j['error']:
            self.error(_("Error converting the link"))

        pyfile.name = j['filename']
        self.link   = j['generated']

        if host in self.SINGLE_CHUNK_HOSTERS:
            self.chunkLimit = 1
        else:
            self.setup()


    @staticmethod
    def _get_host(url):
        host = urlsplit(url).netloc
        return re.search(r'[\w-]+\.\w+$', host).group(0)
