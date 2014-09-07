# -*- coding: utf-8 -*-

import re

from pyload.utils import json_loads
from pyload.plugins.Hoster import Hoster


class MultiDebridCom(Hoster):
    __name__ = "MultiDebridCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'

    __description__ = """Multi-debrid.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Multi-debrid.com")
            self.fail("No Multi-debrid.com account provided")
        else:
            self.logDebug("Original URL: %s" % pyfile.url)
            page = self.req.load('http://multi-debrid.com/api.php',
                                 get={'user': self.user, 'pass': self.account.getAccountData(self.user)['password'],
                                      'link': pyfile.url})
            self.logDebug("JSON data: " + page)
            page = json_loads(page)
            if page['status'] != 'ok':
                self.fail('Unable to unrestrict link')
            new_url = page['link']

        if new_url != pyfile.url:
            self.logDebug("Unrestricted URL: " + new_url)

        self.download(new_url, disposition=True)
