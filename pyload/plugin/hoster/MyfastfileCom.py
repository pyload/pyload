# -*- coding: utf-8 -*-

import re

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster


class MyfastfileCom(MultiHoster):
    __name    = "MyfastfileCom"
    __type    = "hoster"
    __version = "0.08"

    __pattern = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Myfastfile.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]



    def setup(self):
        self.chunkLimit = -1


    def handlePremium(self, pyfile):
        self.html = self.load('http://myfastfile.com/api.php',
                         get={'user': self.user, 'pass': self.account.getAccountData(self.user)['password'],
                              'link': pyfile.url})
        self.logDebug("JSON data: " + self.html)

        self.html = json_loads(self.html)
        if self.html['status'] != 'ok':
            self.fail(_("Unable to unrestrict link"))

        self.link = self.html['link']
