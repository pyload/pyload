# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster
from module.plugins.internal.misc import json


class MyfastfileCom(MultiHoster):
    __name__    = "MyfastfileCom"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Myfastfile.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.chunk_limit = -1


    def handle_premium(self, pyfile):
        self.data = self.load('http://myfastfile.com/api.php',
                         get={'user': self.account.user,
                              'pass': self.account.get_login('password'),
                              'link': pyfile.url})
        self.log_debug("JSON data: " + self.data)

        self.data = json.loads(self.data)
        if self.data['status'] != 'ok':
            self.fail(_("Unable to unrestrict link"))

        self.link = self.data['link']
