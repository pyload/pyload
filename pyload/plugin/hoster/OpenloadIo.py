# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class OpenloadIo(SimpleHoster):
    __name    = "OpenloadIo"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'https?://(?:www\.)?openload\.io/f/\w{11}'

    __description = """Openload.io hoster plugin"""
    __license     = "GPLv3"
    __authors     = [(None, None)]


    NAME_PATTERN = r'<span id="filename">(?P<N>.+)</'
    SIZE_PATTERN = r'<span class="count">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r">(We can't find the file you are looking for)"

    LINK_FREE_PATTERN = r'id="realdownload"><a href="(https?://[\w\.]+\.openload\.io/dl/.*?)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
