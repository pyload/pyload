# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class MyfastfileCom(MultiHoster):
    __name__    = "MyfastfileCom"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Myfastfile.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.chunk_limit = -1


    def handle_premium(self, pyfile):
        self.html = self.load('http://myfastfile.com/api.php',
                         get={'user': self.user, 'pass': self.account.get_info(self.user)['login']['password'],
                              'link': pyfile.url})
        self.log_debug("JSON data: " + self.html)

        self.html = json_loads(self.html)
        if self.html['status'] != 'ok':
            self.fail(_("Unable to unrestrict link"))

        self.link = self.html['link']


getInfo = create_getInfo(MyfastfileCom)
