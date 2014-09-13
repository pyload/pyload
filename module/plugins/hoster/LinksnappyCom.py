# -*- coding: utf-8 -*-

import re

from urlparse import urlsplit

from module.common.json_layer import json_loads, json_dumps
from module.plugins.Hoster import Hoster


class LinksnappyCom(Hoster):
    __name__ = "LinksnappyCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:[^/]*\.)?linksnappy\.com'

    __description__ = """Linksnappy.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    SINGLE_CHUNK_HOSTERS = ('easybytez.com')


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Linksnappy.com")
            self.fail("No Linksnappy.com account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            host = self._get_host(pyfile.url)
            json_params = json_dumps({'link': pyfile.url,
                                      'type': host,
                                      'username': self.user,
                                      'password': self.account.getAccountData(self.user)['password']})
            r = self.load('http://gen.linksnappy.com/genAPI.php',
                          post={'genLinks': json_params})
            self.logDebug("JSON data: " + r)

            j = json_loads(r)['links'][0]

            if j['error']:
                self.logError('Error converting the link: %s' % j['error'])
                self.fail('Error converting the link')

            pyfile.name = j['filename']
            new_url = j['generated']

            if host in self.SINGLE_CHUNK_HOSTERS:
                self.chunkLimit = 1
            else:
                self.setup()

        if new_url != pyfile.url:
            self.logDebug("New URL: " + new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload({"html302": "<title>302 Found</title>"})
        if check == "html302":
            self.retry(wait_time=5, reason="Linksnappy returns only HTML data.")

    @staticmethod
    def _get_host(url):
        host = urlsplit(url).netloc
        return re.search(r'[\w-]+\.\w+$', host).group(0)
