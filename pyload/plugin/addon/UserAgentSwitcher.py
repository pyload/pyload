# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import pycurl
import random

from pyload.plugin.Addon import Addon
from pyload.utils import fs_encode


class UserAgentSwitcher(Addon):
    __name    = "UserAgentSwitcher"
    __type    = "addon"
    __version = "0.04"

    __config = [("activated", "bool", "Activated"               , True                                                                      ),
                  ("uaf"      , "file", "Random user-agents file" , ""                                                                        ),
                  ("uar"      , "bool", "Random user-agent"       , False                                                                     ),
                  ("uas"      , "str" , "Custom user-agent string", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0")]

    __description = """Custom user-agent"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


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
