# -*- coding: utf-8 -*-

import pycurl

from module.plugins.internal.Hook import Hook


class UserAgentSwitcher(Hook):
    __name__    = "UserAgentSwitcher"
    __type__    = "hook"
    __version__ = "0.10"

    __config__ = [("activated"     , "bool", "Activated"                             , True                                                                      ),
                  ("connecttimeout", "int" , "Connection timeout in seconds"         , 60                                                                        ),
                  ("maxredirs"     , "int" , "Maximum number of redirects to follow" , 10                                                                        ),
                  ("useragent"     , "str" , "Custom user-agent string"              , "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0")]

    __description__ = """Custom user-agent"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    interval = 0  #@TODO: Remove in 0.4.10


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def download_preparing(self, pyfile):
        connecttimeout = self.get_config('connecttimeout')
        maxredirs      = self.get_config('maxredirs')
        useragent      = self.get_config('useragent')

        if connecttimeout:
            pyfile.plugin.req.http.c.setopt(pycurl.CONNECTTIMEOUT, connecttimeout)

        if maxredirs:
            pyfile.plugin.req.http.c.setopt(pycurl.MAXREDIRS, maxredirs)

        if useragent:
            self.log_debug("Use custom user-agent string: " + useragent)
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, useragent)
