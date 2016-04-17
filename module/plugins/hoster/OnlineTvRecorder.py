# -*- coding: utf-8 -*-

import re

from module.plugins.hoster.Http import Http
from module.network.HTTPRequest import BadHeader

# Support onlinetvrecorder.com

class OnlineTvRecorder(Http):
    __name__    = "OnlineTvRecorder"
    __type__    = "hoster"
    __version__ = "0.01"
    __status__  = "testing"

    # RIPE Database:
    # inetnum: 81.95.11.0 - 81.95.11.63
    # route:   81.95.8.0/21
    __pattern__ = r'http://81\.95\.11\.\d{1,2}/download/\d+/\d+/\d*/[0-9a-f]+/.+'
    __config__  = [("activated", "bool", "Activated", True)]
    __description__ = """OnlineTvRecorder hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Tim Gregory", "bogeyman@valar.de")]

    def setup(self):
        # OnlineTvRecorder policy
        self.multiDL        = False
        self.chunk_limit     = 1
        self.resume_download = True

    def process(self, pyfile):
        try:
            return super(OnlineTvRecorder, self).process(pyfile)

        except BadHeader, e:
            self.log_debug("OnlineTvRecorder httpcode: %d" % e.code)
            if e.code == 503:
                # max queueing for 3 hours
                self.retry(360, 30, _("Waiting in download queue"))
