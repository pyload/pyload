# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import pycurl
import random

from module.plugins.Hook import Hook
from module.utils import fs_encode


class UserAgentSwitcher(Hook):
    __name__    = "UserAgentSwitcher"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("activated", "bool", "Activated"               , True                                                                      ),
                  ("uaf"      , "file", "Random user-agents file" , ""                                                                        ),
                  ("uar"      , "bool", "Random user-agent"       , False                                                                     ),
                  ("uas"      , "str" , "Custom user-agent string", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0")]

    __description__ = """Custom user-agent"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def downloadPreparing(self, pyfile):
        uar = self.getConfig('uar')
        uaf = fs_encode(self.getConfig('uaf'))

        if uar and os.path.isfile(uaf):
            with open(uaf) as f:
                uas = random.choice([ua for ua in f.read().splitlines()])
        else:
            uas = self.getConfig('uas')

        if uas:
            self.logDebug("Use custom user-agent string: " + uas)
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, uas.encode('utf-8'))
