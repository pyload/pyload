# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MyfastfileCom(SimpleHoster):
    __name__    = "MyfastfileCom"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'

    __description__ = """Myfastfile.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    MULTI_HOSTER = True


    def setup(self):
        self.chunkLimit     = -1
        self.resumeDownload = True


    def handleMulti(self):
        self.logDebug("Original URL: %s" % self.pyfile.url)

        page = self.load('http://myfastfile.com/api.php',
                         get={'user': self.user, 'pass': self.account.getAccountData(self.user)['password'],
                              'link': self.pyfile.url})
        self.logDebug("JSON data: " + page)
        page = json_loads(page)
        if page['status'] != 'ok':
            self.fail(_("Unable to unrestrict link"))
        self.link = page['link']

        if self.link != self.pyfile.url:
            self.logDebug("Unrestricted URL: " + self.link)


getInfo = create_getInfo(MyfastfileCom)
