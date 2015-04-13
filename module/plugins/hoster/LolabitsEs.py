# -*- coding: utf-8 -*

import HTMLParser
import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LolabitsEs(SimpleHoster):
    __name__    = "LolabitsEs"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?lolabits\.es/.+'

    __description__ = """Lolabits.es hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'Descargar: <b>(?P<N>.+?)<'
    SIZE_PATTERN    = r'class="fileSize">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Un usuario con este nombre no existe'

    FILEID_PATTERN = r'name="FileId" value="(\d+)"'
    TOKEN_PATTERN  = r'name="__RequestVerificationToken" type="hidden" value="(.+?)"'
    LINK_PATTERN   = r'"redirectUrl":"(.+?)"'


    def setup(self):
        self.chunkLimit = 1


    def handleFree(self, pyfile):
        fileid = re.search(self.FILEID_PATTERN, self.html).group(1)
        self.logDebug("FileID: " + fileid)

        token = re.search(self.TOKEN_PATTERN, self.html).group(1)
        self.logDebug("Token: " + token)

        self.html = self.load("http://lolabits.es/action/License/Download",
                              post={'fileId'                     : fileid,
                                    '__RequestVerificationToken' : token}).decode('unicode-escape')

        self.link = HTMLParser.HTMLParser().unescape(re.search(self.LINK_PATTERN, self.html).group(1))


getInfo = create_getInfo(LolabitsEs)
