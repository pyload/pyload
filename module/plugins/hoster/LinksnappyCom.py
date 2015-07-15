# -*- coding: utf-8 -*-

import re
import urlparse

from module.common.json_layer import json_loads, json_dumps
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class LinksnappyCom(MultiHoster):
    __name__    = "LinksnappyCom"
    __type__    = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://(?:[^/]+\.)?linksnappy\.com'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Linksnappy.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it", "bilalghouri")]


    #SINGLE_CHUNK_HOSTERS = ["easybytez.com"]


    def handlePremium(self, pyfile):
        host        = self._get_host(pyfile.url)
        json_params = json_dumps({'link'    : pyfile.url,
                                  'type'    : host,
                                  'username': self.user,
                                  'password': self.account.getAccountData(self.user)['password']})

        r = self.load("http://linksnappy.com/api/linkgen",
                      post={'genLinks': json_params})

        self.logDebug("JSON data: " + r)

        j = json_loads(r)['links'][0]

        if j['error']:
            self.error(_("Error converting the link"))

        pyfile.name = j['filename']
        self.link   = j['generated']
        self.setup()
        #if host in self.SINGLE_CHUNK_HOSTERS:
        #    self.chunkLimit = 1
        #else:
        #    self.setup()


    @staticmethod
    def _get_host(url):
        host = urlparse.urlsplit(url).netloc
        return re.search(r'[\w-]+\.\w+$', host).group(0)


getInfo = create_getInfo(LinksnappyCom)
