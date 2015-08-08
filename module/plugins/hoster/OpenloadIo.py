# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OpenloadIo(SimpleHoster):
    __name__    = "OpenloadIo"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?openload\.io/f/[\w_-]{11}'

    __description__ = """Openload.io hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [(None, None)]


    NAME_PATTERN    = r'<span id="filename">(?P<N>.+?)</'
    SIZE_PATTERN    = r'<span class="count">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r">(We can't find the file you are looking for)"

    LINK_FREE_PATTERN = r'id="real\w*download"><a href="(https?://[\w\.]+\.openload\.io/dl/.*?)"'


    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1


getInfo = create_getInfo(OpenloadIo)
