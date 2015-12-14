# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class UserscloudCom(SimpleHoster):
    __name__    = "UserscloudCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?userscloud\.com/\w{12}'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Userscloud.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", None)]


    NAME_PATTERN    = r'<h2 class="strong margin-none">(?P<N>.+?)<'
    SIZE_PATTERN    = r'<div class="ribbon">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r'The file you are trying to download is no longer available'


    def setup(self):
        self.multiDL         = True
        self.resume_download = False
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        self.download(pyfile.url,
                      post=dict(re.findall(r'<input type="hidden" name="(.+?)" value="(.*?)">', self.data)))
