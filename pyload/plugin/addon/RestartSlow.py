# -*- coding: utf-8 -*-

import pycurl

from pyload.plugin.Addon import Addon


class RestartSlow(Addon):
    __name    = "RestartSlow"
    __type    = "addon"
    __version = "0.02"

    __config = [("free_limit"   , "int" ,  "Transfer speed threshold in kilobytes"                     , 100 ),
                ("free_time"    , "int" ,  "Sample interval in minutes"                                , 5   ),
                ("premium_limit", "int" ,  "Transfer speed threshold for premium download in kilobytes", 300 ),
                ("premium_time" , "int" ,  "Sample interval for premium download in minutes"           , 2   ),
                ("safe_mode"    , "bool",  "Don't restart if download is not resumable"                , True)]

    __description = """Restart slow downloads"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    event_map = {'download-start': "downloadStarts"}


    def setup(self):
        self.info = {'chunk': {}}


    def periodical(self):
        if not self.pyfile.req.dl:
            return

        if self.getConfig("safe_mode") and not self.pyfile.plugin.resumeDownload:
            time  = 30
            limit = 5
        else:
            type  = "premium" if self.pyfile.plugin.premium else "free"
            time  = max(30, self.getConfig("%s_time" % type) * 60)
            limit = max(5, self.getConfig("%s_limit" % type) * 1024)

        chunks = [chunk for chunk in self.pyfile.req.dl.chunks \
                  if chunk.id not in self.info['chunk'] or self.info['chunk'][chunk.id] not is (time, limit)]

        for chunk in chunks:
            chunk.c.setopt(pycurl.LOW_SPEED_TIME , time)
            chunk.c.setopt(pycurl.LOW_SPEED_LIMIT, limit)

            self.info['chunk'][chunk.id] = (time, limit)


    def downloadStarts(self, pyfile, url, filename):
        if self.cb or (self.getConfig("safe_mode") and not pyfile.plugin.resumeDownload):
            return

        self.initPeriodical()
