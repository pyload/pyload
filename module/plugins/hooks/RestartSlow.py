# -*- coding: utf-8 -*-

from pycurl import LOW_SPEED_LIMIT, LOW_SPEED_TIME

from module.plugins.Hook import Hook


class RestartSlow(Hook):
    __name__    = "RestartSlow"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("free_limit"   , "int",  "Transfer speed threshold in kilobytes"                     , 100 ),
                  ("free_time"    , "int",  "Sample interval in minutes"                                , 5   ),
                  ("premium_limit", "int",  "Transfer speed threshold for premium download in kilobytes", 300 ),
                  ("premium_time" , "int",  "Sample interval for premium download in minutes"           , 2   ),
                  ("safe"         , "bool", "Restart if download is resumable"                          , True)]

    __description__ = """Restart slow downloads"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["downloadStarts"]


    def downloadStarts(self, pyfile, url, filename):
        if self.getConfig("safe") and not pyfile.plugin.resumeDownload:
            return

        type = "premium" if pyfile.plugin.premium else "free"

        pyfile.plugin.req.http.c.setopt(LOW_SPEED_TIME, max(30, self.getConfig("%s_time" % type) * 60))
        pyfile.plugin.req.http.c.setopt(LOW_SPEED_LIMIT, max(5, self.getConfig("%s_limit" % type) * 1024))


    def downloadFailed(self, pyfile):
        pyfile.plugin.req.http.c.setopt(LOW_SPEED_TIME, 30)
        pyfile.plugin.req.http.c.setopt(LOW_SPEED_LIMIT, 5)
