# -*- coding: utf-8 -*-

import pycurl

from module.plugins.Hook import Hook


class UserAgentSwitcher(Hook):
    __name__    = "UserAgentSwitcher"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("ua", "str", "Custom user-agent string", "")]

    __description__ = """Custom user-agent"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def downloadPreparing(self, pyfile):
        ua = self.getConfig('ua')
        if ua:
            self.logDebug("Use custom user-agent string: " + ua)
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, ua)
