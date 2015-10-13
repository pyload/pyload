# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UserscloudCom(SimpleHoster):
    __name__    = "UserscloudCom"
    __type__    = "hoster"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?userscloud\.com/\w{12}'
    __config__  = [("activated", "bool", "Activated", True)]

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
                      post=dict(re.findall(r'<input type="hidden" name="(.+?)" value="(.*?)">', self.html)))


getInfo = create_getInfo(UserscloudCom)
