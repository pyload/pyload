# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class TwoSharedCom(SimpleHoster):
    __name__    = "TwoSharedCom"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?2shared\.com/(account/)?(download|get|file|document|photo|video|audio)/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """2Shared.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN    = r'<h1>(?P<N>.*)</h1>'
    SIZE_PATTERN    = r'<span class="dtitle">File size:</span>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted\.'

    LINK_FREE_PATTERN = r'window.location =\'(.+?)\';'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


getInfo = create_getInfo(TwoSharedCom)
