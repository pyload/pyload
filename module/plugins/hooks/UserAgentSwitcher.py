# -*- coding: utf-8 -*-

import pycurl

from module.plugins.Hook import Hook
from module.utils import encode


class UserAgentSwitcher(Hook):
    __name__    = "UserAgentSwitcher"
    __type__    = "hook"
    __version__ = "0.05"

    __config__ = [("activated", "bool", "Activated"                , True                                                                      ),
                  ("useragent", "str" , "Custom user-agent string" , "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0")]

    __description__ = """Custom user-agent"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def downloadPreparing(self, pyfile):
        useragent = encode(self.getConfig('useragent'))
        if useragent:
            self.logDebug("Use custom user-agent string: " + useragent)
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, useragent)
