# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OpenloadIo(SimpleHoster):
    __name__    = "OpenloadIo"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?openload\.io/f/\w{11}'

    __description__ = """Openload.io hoster plugin"""
    __license__     = "GPLv3"

    NAME_PATTERN = r'<span id="filename">(?P<N>.+)</'
    SIZE_PATTERN = r'<span class="count">(?P<S>[\d.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r">(We can't find the file you are looking for)"

    LINK_FREE_PATTERN = r'id="realdownload"><a href="(https?://[\w\.]+\.openload\.io/dl/.*?)"'

    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1

getInfo = create_getInfo(OpenloadIo)
