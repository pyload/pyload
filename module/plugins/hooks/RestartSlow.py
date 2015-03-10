# -*- coding: utf-8 -*-

import pycurl

from module.plugins.Hook import Hook


class RestartSlow(Hook):
    __name__    = "RestartSlow"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("free_limit"   , "int" ,  "Transfer speed threshold in kilobytes"                     , 100 ),
                  ("free_time"    , "int" ,  "Sample interval in minutes"                                , 5   ),
                  ("premium_limit", "int" ,  "Transfer speed threshold for premium download in kilobytes", 300 ),
                  ("premium_time" , "int" ,  "Sample interval for premium download in minutes"           , 2   ),
                  ("safe_mode"    , "bool",  "Don't restart if download is not resumable"                , True)]

    __description__ = """Restart slow downloads"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    event_list = ["downloadStarts"]


    def setup(self):
        self.info = {'chunk': {}}


    def initPeriodical(self):
        pass


    def periodical(self):
        if not self.pyfile.plugin.req.dl:
            return

        if self.getConfig('safe_mode') and not self.pyfile.plugin.resumeDownload:
            time  = 30
            limit = 5
        else:
            type  = "premium" if self.pyfile.plugin.premium else "free"
            time  = max(30, self.getConfig("%s_time" % type) * 60)
            limit = max(5, self.getConfig("%s_limit" % type) * 1024)

        chunks = [chunk for chunk in self.pyfile.plugin.req.dl.chunks \
                  if chunk.id not in self.info['chunk'] or self.info['chunk'][chunk.id] is not (time, limit)]

        for chunk in chunks:
            chunk.c.setopt(pycurl.LOW_SPEED_TIME , time)
            chunk.c.setopt(pycurl.LOW_SPEED_LIMIT, limit)

            self.info['chunk'][chunk.id] = (time, limit)


    def downloadStarts(self, pyfile, url, filename):
        if self.cb or (self.getConfig('safe_mode') and not pyfile.plugin.resumeDownload):
            return
        self.pyfile = pyfile
        super(RestartSlow, self).initPeriodical()
