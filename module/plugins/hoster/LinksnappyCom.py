# -*- coding: utf-8 -*-

import re

from urlparse import urlsplit

from module.common.json_layer import json_loads, json_dumps
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LinksnappyCom(SimpleHoster):
    __name__    = "LinksnappyCom"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:[^/]*\.)?linksnappy\.com'

    __description__ = """Linksnappy.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    SINGLE_CHUNK_HOSTERS = ('easybytez.com')


    def setup(self):
        self.chunkLimit     = -1
        self.resumeDownload = True


    def handleMulti(self):
        host = self._get_host(self.pyfile.url)
        json_params = json_dumps({'link': self.pyfile.url,
                                  'type': host,
                                  'username': self.user,
                                  'password': self.account.getAccountData(self.user)['password']})
        r = self.load('http://gen.linksnappy.com/genAPI.php',
                      post={'genLinks': json_params})
        self.logDebug("JSON data: " + r)

        j = json_loads(r)['links'][0]

        if j['error']:
            msg = _("Error converting the link")
            self.logError(msg, j['error'])
            self.fail(msg)

        self.pyfile.name = j['filename']
        self.link = j['generated']

        if host in self.SINGLE_CHUNK_HOSTERS:
            self.chunkLimit = 1
        else:
            self.setup()

        if self.link != self.pyfile.url:
            self.logDebug("New URL: " + self.link)


    def checkFile(self):
        check = self.checkDownload({"html302": "<title>302 Found</title>"})

        if check == "html302":
            self.retry(wait_time=5, reason=_("Linksnappy returns only HTML data"))


    @staticmethod
    def _get_host(url):
        host = urlsplit(url).netloc
        return re.search(r'[\w-]+\.\w+$', host).group(0)


getInfo = create_getInfo(LinksnappyCom)
